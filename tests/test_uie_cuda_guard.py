import unittest
from equipment_ie.uie_cuda_guard import LIB_ROOT, LOADER, require_isolated_runtime


class UIECudaGuardTest(unittest.TestCase):
    def report(self):
        return {'compiled_cuda': '11.8', 'compiled_cudnn': '8.6.0',
                'isolated_cudnn_version': 8600, 'paddle_runtime_cudnn_version': 8600,
                'FLAGS_cudnn_dir': str(LOADER), 'FLAGS_cuda_dir': str(LOADER),
                'loaded_cuda_library_paths': [str(LIB_ROOT/'cudnn/lib/libcudnn.so.8')]}

    def test_matching_actual_runtime_and_path_pass(self):
        report = self.report()
        self.assertIs(require_isolated_runtime(report), report)

    def test_previous_import_pass_runtime9_regression(self):
        report = self.report()
        report['paddle_runtime_cudnn_version'] = 90100
        with self.assertRaises(RuntimeError):
            require_isolated_runtime(report)

    def test_system_mapping_even_with_matching_version_stops(self):
        report = self.report()
        report['loaded_cuda_library_paths'].append('/usr/lib/x86_64-linux-gnu/libcublas.so.11')
        with self.assertRaises(RuntimeError):
            require_isolated_runtime(report)

    def test_missing_process_local_flags_stops(self):
        for name in ('FLAGS_cudnn_dir', 'FLAGS_cuda_dir'):
            report = self.report()
            report[name] = None
            with self.assertRaises(RuntimeError):
                require_isolated_runtime(report)

    def test_compile_target_change_stops(self):
        report = self.report()
        report['compiled_cuda'] = '12.4'
        with self.assertRaises(RuntimeError):
            require_isolated_runtime(report)

    def test_missing_runtime_mapping_stops(self):
        report = self.report()
        report['loaded_cuda_library_paths'] = []
        with self.assertRaises(RuntimeError):
            require_isolated_runtime(report)


if __name__ == '__main__':
    unittest.main()
