// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

'use strict';

console.log('_KARMA_ARGS:' + process.argv)

module.exports = function(config) {
    config.set({
      files: [
        { pattern: 'onnxruntime_test_all.js', watched: false },
        { pattern: 'onnxruntime_test_all.data', included: false },
        { pattern: 'onnxruntime_test_all.wasm', included: false },
      ],
      basePath: '.',
      proxies: {
        '/onnxruntime_test_all.data': '/base/onnxruntime_test_all.data'
      },
      plugins: [require('karma-chrome-launcher')],
      browsers: ['ChromeTest'],
      client: { captureConsole: true },
      customLaunchers: {
        ChromeTest: {
          base: 'ChromeCanary'
        }
      }
      //...
    });
  };
