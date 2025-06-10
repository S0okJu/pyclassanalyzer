import argparse
import os
import sys
from pyclassanalyzer.analyzer.class_structure import ClassAnalyzer

def main():
    parser = argparse.ArgumentParser(description='Python 클래스 구조 분석 및 PlantUML 다이어그램 생성')
    parser.add_argument('path', help='분석할 Python 파일 또는 디렉토리 경로')
    parser.add_argument('-o', '--output', default='class_diagram.puml', help='출력할 PlantUML 파일 경로 (기본값: class_diagram.puml)')
    parser.add_argument('--no-attributes', action='store_true', help='속성 표시 제외')
    parser.add_argument('--no-methods', action='store_true', help='메서드 표시 제외')
    parser.add_argument('--summary', action='store_true', help='분석 결과 요약 출력')
    
    args = parser.parse_args()
    
    try:
        analyzer = ClassAnalyzer()
        
        if os.path.isfile(args.path):
            analyzer.analyze_file(args.path)
        else:
            analyzer.analyze_directory(args.path)
        
        # 속성과 메서드는 기본적으로 표시 (--no-attributes나 --no-methods 옵션이 없을 때)
        analyzer.generate_diagram(
            output_file=args.output,
            include_attributes=not args.no_attributes,
            include_methods=not args.no_methods
        )
        
        if args.summary:
            analyzer.print_analysis_summary()
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
        
    return 0

if __name__ == '__main__':
    sys.exit(main()) 