// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

#pragma once

#include "core/providers/rocm/tunable/rocm_tunable.h"

namespace onnxruntime {
namespace contrib {
namespace rocm {

// template <typename T>
// struct GemmSoftmaxGemmPermuteParams : onnxruntime::rocm::tunable::OpParams {
//   using StrideT = std::array<T, 4>;

//   int64_t batch;            // B
//   int64_t sequence_length;  // S
//   int64_t num_heads;        // N
//   int64_t head_dim;         // H
//   const T* q;               // [B, N, S, H]
//   const T* k;               // [B, N, S, H]
//   const T* v;               // [B, N, S, H]
//   const T* attention_mask;  // [B, S]
//   T* out;                   // [B, S, N, H]
//   StrideT q_strides;        // Q strides
//   StrideT k_strides;        // K strides
//   StrideT v_strides;        // V strides
//   StrideT out_strides;      // out strides
//   float scale;
// };

// template<typename T>
// Status RocblasGemmSoftmaxGemmPermute(const GemmSoftmaxGemmPermuteParams<T>* params);

// template<typename T>
// Status GemmSoftmaxGemmPermuteTunableOp(const GemmSoftmaxGemmPermuteParams<T>* params);

}  // namespace rocm
}  // namespace contrib
}  // namespace onnxruntime
