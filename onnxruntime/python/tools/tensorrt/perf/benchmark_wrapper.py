import argparse
import copy
import csv
import json
import logging
import os
import pprint
import re

import coloredlogs
from benchmark import *
from perf_utils import *


def write_model_info_to_file(model, path):
    with open(path, "w") as file:
        file.write(json.dumps(model))  # use `json.loads` to do the reverse


def get_ep_list(comparison):
    if comparison == "acl":
        ep_list = [cpu, acl]
    else:
        # test with cuda and trt
        ep_list = [
            cpu,
            cuda,
            trt,
            standalone_trt,
            cuda_fp16,
            trt_fp16,
            standalone_trt_fp16,
        ]
    return ep_list


def resolve_trtexec_path(workspace):
    trtexec_options = get_output(["find", workspace, "-name", "trtexec"])
    trtexec_path = re.search(r".*/bin/trtexec", trtexec_options).group(0)
    logger.info("using trtexec {}".format(trtexec_path))
    return trtexec_path


def dict_to_args(dct):
    return ",".join(["{}={}".format(k, v) for k, v in dct.items()])


def main():
    args = parse_arguments()
    setup_logger(False)
    pp = pprint.PrettyPrinter(indent=4)

    # create ep list to iterate through
    if args.ep_list:
        ep_list = args.ep_list
    else:
        ep_list = get_ep_list(args.comparison)

    trtexec = resolve_trtexec_path(args.workspace)

    models = {}
    parse_models_helper(args, models)

    model_to_fail_ep = {}

    benchmark_fail_csv = fail_name + csv_ending
    benchmark_metrics_csv = metrics_name + csv_ending
    benchmark_success_csv = success_name + csv_ending
    benchmark_latency_csv = latency_name + csv_ending
    benchmark_status_csv = status_name + csv_ending
    benchmark_session_csv = session_name + csv_ending
    specs_csv = specs_name + csv_ending

    validate = is_validate_mode(args.running_mode)
    benchmark = is_benchmark_mode(args.running_mode)

    for model, model_info in models.items():
        logger.info("\n" + "=" * 40 + "=" * len(model))
        logger.info("=" * 20 + model + "=" * 20)
        logger.info("=" * 40 + "=" * len(model))

        model_info["model_name"] = model

        model_list_file = os.path.join(os.getcwd(), model + ".json")
        write_model_info_to_file([model_info], model_list_file)

        for ep in ep_list:
            command = [
                "python3",
                "benchmark.py",
                "-r",
                args.running_mode,
                "-m",
                model_list_file,
                "-o",
                args.perf_result_path,
                "--ep",
                ep,
                "--write_test_result",
                "false",
            ]

            if args.track_memory:
                command.append("-z")

            if ep == standalone_trt or ep == standalone_trt_fp16:
                command.extend(["--trtexec", trtexec])

            if len(args.cuda_ep_options):
                command.extend(["--cuda_ep_options", dict_to_args(args.cuda_ep_options)])

            if len(args.trt_ep_options):
                command.extend(["--trt_ep_options", dict_to_args(args.trt_ep_options)])

            if validate:
                command.extend(["--benchmark_metrics_csv", benchmark_metrics_csv])

            if benchmark:
                command.extend(
                    [
                        "-t",
                        str(args.test_times),
                        "-o",
                        args.perf_result_path,
                        "--write_test_result",
                        "false",
                        "--benchmark_fail_csv",
                        benchmark_fail_csv,
                        "--benchmark_latency_csv",
                        benchmark_latency_csv,
                        "--benchmark_success_csv",
                        benchmark_success_csv,
                    ]
                )

            p = subprocess.run(command, stderr=subprocess.PIPE)
            logger.info("Completed subprocess %s ", " ".join(p.args))
            logger.info("Return code: %d", p.returncode)

            if p.returncode != 0:
                error_type = "runtime error"
                error_message = "Benchmark script exited with returncode = " + str(p.returncode)

                if p.stderr:
                    error_message += "\nSTDERR:\n" + p.stderr.decode("utf-8")

                logger.error(error_message)
                update_fail_model_map(model_to_fail_ep, model, ep, error_type, error_message)
                write_map_to_file(model_to_fail_ep, FAIL_MODEL_FILE)
                logger.info(model_to_fail_ep)

        os.remove(model_list_file)

    path = os.path.join(os.getcwd(), args.perf_result_path)
    if not os.path.exists(path):
        from pathlib import Path

        Path(path).mkdir(parents=True, exist_ok=True)

    if validate:
        logger.info("\n=========================================")
        logger.info("=========== Models/EPs metrics ==========")
        logger.info("=========================================")

        if os.path.exists(METRICS_FILE):
            model_to_metrics = read_map_from_file(METRICS_FILE)
            output_metrics(model_to_metrics, os.path.join(path, benchmark_metrics_csv))
            logger.info("\nSaved model metrics results to {}".format(benchmark_metrics_csv))

    if benchmark:
        logger.info("\n=========================================")
        logger.info("======= Models/EPs session creation =======")
        logger.info("=========================================")

        if os.path.exists(SESSION_FILE):
            model_to_session = read_map_from_file(SESSION_FILE)
            pretty_print(pp, model_to_session)
            output_session_creation(model_to_session, os.path.join(path, benchmark_session_csv))
            logger.info("\nSaved session creation results to {}".format(benchmark_session_csv))

        logger.info("\n=========================================================")
        logger.info("========== Failing Models/EPs (accumulated) ==============")
        logger.info("==========================================================")

        if os.path.exists(FAIL_MODEL_FILE) or len(model_to_fail_ep) > 1:
            model_to_fail_ep = read_map_from_file(FAIL_MODEL_FILE)
            output_fail(model_to_fail_ep, os.path.join(path, benchmark_fail_csv))
            logger.info(model_to_fail_ep)
            logger.info("\nSaved model failing results to {}".format(benchmark_fail_csv))

        logger.info("\n=======================================================")
        logger.info("=========== Models/EPs Status (accumulated) ===========")
        logger.info("=======================================================")

        model_status = {}
        if os.path.exists(LATENCY_FILE):
            model_latency = read_map_from_file(LATENCY_FILE)
            is_fail = False
            model_status = build_status(model_status, model_latency, is_fail)
        if os.path.exists(FAIL_MODEL_FILE):
            model_fail = read_map_from_file(FAIL_MODEL_FILE)
            is_fail = True
            model_status = build_status(model_status, model_fail, is_fail)

        pretty_print(pp, model_status)

        output_status(model_status, os.path.join(path, benchmark_status_csv))
        logger.info("\nSaved model status results to {}".format(benchmark_status_csv))

        logger.info("\n=========================================================")
        logger.info("=========== Models/EPs latency (accumulated)  ===========")
        logger.info("=========================================================")

        if os.path.exists(LATENCY_FILE):
            model_to_latency = read_map_from_file(LATENCY_FILE)
            add_improvement_information(model_to_latency)

            pretty_print(pp, model_to_latency)

            output_latency(model_to_latency, os.path.join(path, benchmark_latency_csv))
            logger.info("\nSaved model latency results to {}".format(benchmark_latency_csv))

    logger.info("\n===========================================")
    logger.info("=========== System information  ===========")
    logger.info("===========================================")
    info = get_system_info(args)
    pretty_print(pp, info)
    logger.info("\n")
    output_specs(info, os.path.join(path, specs_csv))
    logger.info("\nSaved hardware specs to {}".format(specs_csv))


if __name__ == "__main__":
    main()
