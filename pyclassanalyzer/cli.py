import argparse
import sys
import os
import time 
from pathlib import Path

from pyclassanalyzer.scanner.scanner import GraphScanner

def main():
    parser = argparse.ArgumentParser(
        description='Python 클래스 구조 분석 및 PlantUML 다이어그램 생성',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  %(prog)s ./my_project                           # 현재 디렉토리의 my_project 분석
  %(prog)s ./src -o diagrams/classes.puml        # src 디렉토리 분석하고 특정 파일로 저장  
  %(prog)s main.py --summary                     # 단일 파일 분석하고 요약 정보 출력
  %(prog)s ./project -o auto --summary           # 자동 파일명으로 저장하고 요약 출력
        """
    )
    
    parser.add_argument('path', 
                       help='분석할 Python 파일 또는 디렉토리 경로')
    parser.add_argument('-o', '--output', 
                       default='class_diagram.puml', 
                       help='출력할 PlantUML 파일 경로 (기본값: class_diagram.puml, "auto"로 설정시 자동 생성)')
    parser.add_argument('--summary', 
                       action='store_true', 
                       help='분석 결과 요약 출력')
    parser.add_argument('-t', '--title',
                       help='다이어그램 제목 (기본값: 프로젝트 이름 기반 자동 생성)')
    parser.add_argument('--console-only',
                       action='store_true',
                       help='파일 저장 없이 콘솔에만 출력')
    parser.add_argument('--quiet', '-q',
                       action='store_true',
                       help='요약 정보 출력 안함 (조용한 모드)')

    args = parser.parse_args()

    try:
        # 경로 검증
        input_path = Path(args.path)
        if not input_path.exists():
            print(f"Error: 지정된 경로를 찾을 수 없습니다: {args.path}", file=sys.stderr)
            return 1
        
        # 파이썬 파일이나 디렉토리인지 확인
        if input_path.is_file() and not input_path.suffix == '.py':
            print(f"Warning: 지정된 파일이 Python 파일(.py)이 아닙니다: {args.path}")
        
        # GraphScanner 인스턴스 생성
        scanner = GraphScanner(str(input_path))
        
        if not args.quiet:
            print(f"Python 클래스 구조 분석 시작: {args.path}")
            print("-" * 50)
        
        # AST 분석 수행
        scanner.analyze()
        
        # 분석 결과 요약 출력 (요청된 경우)
        if args.summary and not args.quiet:
            scanner.print_analysis_summary()
        
        # 출력 파일 경로 결정
        output_path = None
        if not args.console_only:
            if args.output == 'auto':
                # 자동 파일명 생성
                output_filename = scanner.generate_auto_filename()
                output_path = str(Path.cwd() / output_filename)
            else:
                output_path = args.output
            
            # 출력 디렉토리 생성
            output_dir = Path(output_path).parent
            if not output_dir.exists():
                output_dir.mkdir(parents=True, exist_ok=True)
                if not args.quiet:
                    print(f"출력 디렉토리 생성: {output_dir}")
        
        # PlantUML 다이어그램 생성 및 출력
        if args.console_only:
            # 콘솔에만 출력
            if not args.quiet:
                print("\nPlantUML 다이어그램:")
                print("=" * 50)
            
            content = scanner.get_plantuml_content(args.title)
            print(content)
            
        else:
            # 파일 저장 (및 선택적으로 콘솔 출력)
            if args.quiet:
                # 조용한 모드: 파일로만 저장
                success = scanner.save_plantuml(output_path, args.title)
                if success:
                    print(f"PlantUML 다이어그램 저장: {output_path}")
                else:
                    print(f"Error: 파일 저장 실패: {output_path}", file=sys.stderr)
                    return 1
            else:
                # 일반 모드: 콘솔 출력 + 파일 저장
                scanner.print_plantuml(output_path, args.title)
        
        if not args.quiet:
            print("\n분석 완료!")
            
            # 추가 정보 출력
            node_count = len(scanner.graph.nodes)
            relation_count = len(scanner.graph.relations)
            
            if node_count == 0:
                print("Warning: 분석된 클래스가 없습니다. 경로를 확인해주세요.")
            else:
                print(f"총 {node_count}개의 클래스와 {relation_count}개의 관계를 발견했습니다.")
        
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if not args.quiet:
            import traceback
            print("\n상세 오류 정보:", file=sys.stderr)
            traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())