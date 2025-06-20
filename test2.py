import os
import sys
import inspect
import importlib.util
import ast
from pathlib import Path
from typing import Optional, List, Dict, Any

class ModuleInfoDetector:
    """Python 파일의 모듈 정보를 감지하는 클래스"""
    
    @staticmethod
    def get_current_module_info() -> Dict[str, Any]:
        """현재 실행 중인 모듈의 정보를 반환합니다."""
        frame = inspect.currentframe()
        try:
            # 호출한 프레임 정보 가져오기
            caller_frame = frame.f_back
            
            return {
                'filename': caller_frame.f_globals.get('__file__'),
                'module_name': caller_frame.f_globals.get('__name__'),
                'package': caller_frame.f_globals.get('__package__'),
                'spec': caller_frame.f_globals.get('__spec__'),
                'doc': caller_frame.f_globals.get('__doc__'),
            }
        finally:
            del frame
    
    @staticmethod
    def get_module_name_from_file(file_path: str) -> Optional[str]:
        """파일 경로로부터 모듈명을 추론합니다."""
        path = Path(file_path)
        
        # 1. __init__.py인 경우 디렉토리명이 모듈명
        if path.name == '__init__.py':
            return path.parent.name
        
        # 2. 일반 .py 파일인 경우 파일명이 모듈명
        if path.suffix == '.py':
            return path.stem
        
        return None
    
    @staticmethod
    def get_package_structure(file_path: str) -> Dict[str, Any]:
        """파일이 속한 패키지 구조를 분석합니다."""
        path = Path(file_path).resolve()
        package_parts = []
        current_path = path.parent
        
        # 상위 디렉토리로 올라가며 __init__.py 찾기
        while current_path != current_path.parent:
            init_file = current_path / '__init__.py'
            if init_file.exists():
                package_parts.append(current_path.name)
                current_path = current_path.parent
            else:
                break
        
        # 패키지 경로 역순 정렬
        package_parts.reverse()
        
        # 모듈명 결정
        if path.name == '__init__.py':
            module_name = path.parent.name
        else:
            module_name = path.stem
        
        # 전체 모듈 경로
        full_module_path = '.'.join(package_parts + [module_name]) if package_parts else module_name
        
        return {
            'file_path': str(path),
            'package_parts': package_parts,
            'module_name': module_name,
            'full_module_path': full_module_path,
            'is_package': path.name == '__init__.py',
            'package_root': str(current_path) if package_parts else None
        }
    
    @staticmethod
    def analyze_imports_from_ast(file_path: str) -> Dict[str, List[str]]:
        """AST를 사용하여 파일의 import 구문을 분석합니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = {
                'standard_imports': [],      # import module
                'from_imports': [],          # from module import item
                'relative_imports': [],      # from .module import item
                'imported_modules': set(),   # 모든 import된 모듈들
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports['standard_imports'].append({
                            'module': alias.name,
                            'alias': alias.asname,
                            'lineno': node.lineno
                        })
                        imports['imported_modules'].add(alias.name.split('.')[0])
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    level = node.level
                    
                    import_info = {
                        'module': module,
                        'level': level,
                        'items': [{'name': alias.name, 'alias': alias.asname} 
                                for alias in node.names],
                        'lineno': node.lineno
                    }
                    
                    if level > 0:  # 상대 import
                        imports['relative_imports'].append(import_info)
                    else:  # 절대 import
                        imports['from_imports'].append(import_info)
                    
                    if module:
                        imports['imported_modules'].add(module.split('.')[0])
            
            imports['imported_modules'] = list(imports['imported_modules'])
            return imports
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_module_from_sys_modules(file_path: str) -> Optional[str]:
        """sys.modules에서 파일 경로에 해당하는 모듈을 찾습니다."""
        file_path = os.path.abspath(file_path)
        
        for module_name, module in sys.modules.items():
            if hasattr(module, '__file__') and module.__file__:
                module_file = os.path.abspath(module.__file__)
                if module_file == file_path:
                    return module_name
        
        return None
    
    @staticmethod
    def detect_module_type(file_path: str) -> str:
        """모듈 타입을 감지합니다."""
        path = Path(file_path)
        
        # Python 파일인지 확인
        if path.suffix != '.py':
            return 'not_python'
        
        # __init__.py인지 확인
        if path.name == '__init__.py':
            return 'package_init'
        
        # 테스트 파일인지 확인
        if path.name.startswith('test_') or path.name.endswith('_test.py'):
            return 'test_module'
        
        # __main__.py인지 확인
        if path.name == '__main__.py':
            return 'main_module'
        
        # 설정 파일인지 확인
        if path.name in ['setup.py', 'config.py', 'settings.py']:
            return 'config_module'
        
        return 'regular_module'

class FileScanner:
    """파일을 스캔하면서 모듈 정보를 수집하는 클래스"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
        self.detector = ModuleInfoDetector()
        self.scanned_files = []
    
    def scan_directory(self, directory: str = None) -> List[Dict[str, Any]]:
        """디렉토리를 스캔하여 모든 Python 파일의 모듈 정보를 수집합니다."""
        if directory is None:
            directory = self.base_path
        else:
            directory = Path(directory).resolve()
        
        results = []
        
        for py_file in directory.rglob('*.py'):
            file_info = self.scan_file(str(py_file))
            results.append(file_info)
            self.scanned_files.append(str(py_file))
        
        return results
    
    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """단일 파일을 스캔하여 모듈 정보를 반환합니다."""
        file_path = str(Path(file_path).resolve())
        
        # 현재 스캔 중인 파일 정보
        current_scan_info = {
            'currently_scanning': file_path,
            'scan_timestamp': __import__('datetime').datetime.now().isoformat(),
        }
        
        # 기본 정보 수집
        package_info = self.detector.get_package_structure(file_path)
        module_type = self.detector.detect_module_type(file_path)
        sys_module = self.detector.get_module_from_sys_modules(file_path)
        imports = self.detector.analyze_imports_from_ast(file_path)
        
        return {
            **current_scan_info,
            'file_info': {
                'absolute_path': file_path,
                'relative_path': os.path.relpath(file_path, self.base_path),
                'filename': os.path.basename(file_path),
                'size': os.path.getsize(file_path),
                'modified_time': os.path.getmtime(file_path),
            },
            'module_info': {
                'module_name': package_info['module_name'],
                'full_module_path': package_info['full_module_path'],
                'package_parts': package_info['package_parts'],
                'is_package': package_info['is_package'],
                'module_type': module_type,
                'sys_module_name': sys_module,
            },
            'imports': imports,
        }
    
    def get_current_file_module_info(self) -> Dict[str, Any]:
        """현재 실행 중인 파일의 모듈 정보를 반환합니다."""
        # 호출자의 프레임 정보 가져오기
        frame = inspect.currentframe()
        try:
            caller_frame = frame.f_back
            current_file = caller_frame.f_globals.get('__file__')
            
            if current_file:
                return self.scan_file(current_file)
            else:
                return {'error': 'Cannot determine current file'}
        finally:
            del frame

def demonstrate_module_detection():
    """모듈 감지 기능들을 시연합니다."""
    print("=" * 60)
    print("Python 모듈명 감지 시연")
    print("=" * 60)
    
    # 1. 현재 모듈 정보
    print("\n1. 현재 모듈 정보:")
    print("-" * 30)
    current_info = ModuleInfoDetector.get_current_module_info()
    for key, value in current_info.items():
        print(f"{key}: {value}")
    
    # 2. 파일 경로로부터 모듈명 추론
    print("\n2. 파일 경로로부터 모듈명 추론:")
    print("-" * 30)
    test_paths = [
        "/path/to/project/mypackage/__init__.py",
        "/path/to/project/mypackage/module1.py", 
        "/path/to/project/utils.py",
        "example.py"
    ]
    
    for path in test_paths:
        module_name = ModuleInfoDetector.get_module_name_from_file(path)
        print(f"{path} → {module_name}")
    
    # 3. 현재 파일의 상세 분석
    print("\n3. 현재 파일의 상세 분석:")
    print("-" * 30)
    
    scanner = FileScanner()
    current_file_info = scanner.get_current_file_module_info()
    
    if 'error' not in current_file_info:
        print(f"현재 스캔 중: {current_file_info['currently_scanning']}")
        print(f"모듈명: {current_file_info['module_info']['module_name']}")
        print(f"전체 모듈 경로: {current_file_info['module_info']['full_module_path']}")
        print(f"모듈 타입: {current_file_info['module_info']['module_type']}")
        print(f"패키지 여부: {current_file_info['module_info']['is_package']}")
        
        if current_file_info['imports'].get('imported_modules'):
            print(f"Import된 모듈들: {current_file_info['imports']['imported_modules']}")
    else:
        print(f"오류: {current_file_info['error']}")

# 실제 사용 예제
def example_usage():
    """실제 사용 예제를 보여줍니다."""
    print("\n" + "=" * 60)
    print("실제 사용 예제")
    print("=" * 60)
    
    # 스캐너 생성
    scanner = FileScanner(".")
    
    # 현재 파일 스캔
    print("\n현재 파일 스캔 중...")
    current_info = scanner.get_current_file_module_info()
    
    if 'error' not in current_info:
        print(f"✓ 스캔 완료: {current_info['file_info']['filename']}")
        print(f"  모듈명: {current_info['module_info']['full_module_path']}")
        print(f"  파일 크기: {current_info['file_info']['size']} bytes")
    
    # 예제 파일 분석 (존재한다면)
    example_files = ["__init__.py", "setup.py", "test_example.py"]
    
    for filename in example_files:
        if os.path.exists(filename):
            print(f"\n{filename} 분석 중...")
            file_info = scanner.scan_file(filename)
            print(f"  모듈 타입: {file_info['module_info']['module_type']}")
            print(f"  모듈 경로: {file_info['module_info']['full_module_path']}")

if __name__ == "__main__":
    demonstrate_module_detection()
    example_usage()