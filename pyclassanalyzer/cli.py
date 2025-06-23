import argparse
import sys
import os
from pathlib import Path

from pyclassanalyzer.scanner.scanner import GraphScanner

def main():
    parser = argparse.ArgumentParser(
        description='Python 클래스 구조 분석 및 PlantUML 다이어그램 생성',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument('path', 
                       help='분석할 Python 파일 또는 디렉토리 경로')
    parser.add_argument('-o', '--output',  
                       help='출력할 PlantUML 파일 경로 (기본값: [project_name]_class_diagram_[timestamp].puml")'
                       )
    parser.add_argument('--summary', 
                       action='store_true', 
                       help='분석 결과 요약 출력')
    parser.add_argument('-t', '--title',
                       help='다이어그램 제목 (기본값: 프로젝트 이름 기반 자동 생성)')
    parser.add_argument('--exclude',
                        action='append',
                        help= '제외시킬 폴더')
    args = parser.parse_args()

    try:
        input_path = Path(args.path)
        if not input_path.exists():
            print(f"Error: 지정된 경로를 찾을 수 없습니다: {args.path}", file=sys.stderr)
            return 1
        
        scanner = GraphScanner(str(input_path))  
        if input_path.is_file():
            print(f"Warning: 현재 파일은 지원되지 않습니다.")
            return 1
        elif input_path.is_dir():   
            scanner.analyze()
            
        if args.summary:
            scanner.print_analysis_summary()
        
        output_path = args.output
        if not output_path:
            output_filename = scanner.generate_auto_filename()
            output_path = str(Path.cwd() / output_filename)
        
        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        is_success = scanner.save_plantuml(output_path, args.title)
        if is_success:
            scanner.print_graph_count()
        else:
            print(f"Error: 파일 저장 실패: {output_path}", file=sys.stderr)
            return 1
    
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())