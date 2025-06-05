import argparse
import os
from .analyzer.class_analyzer import ClassAnalyzer

def main():
    parser = argparse.ArgumentParser(description='Analyze Python class structure and generate PlantUML diagram.')
    parser.add_argument('path', help='Path to the Python project directory')
    parser.add_argument('--output', '-o', default='class_diagram.puml',
                      help='Output PlantUML file path (default: class_diagram.puml)')
    parser.add_argument('--no-attributes', action='store_true',
                      help='Exclude attributes from the diagram')
    parser.add_argument('--no-methods', action='store_true',
                      help='Exclude methods from the diagram')
    parser.add_argument('--summary', '-s', action='store_true',
                      help='Print analysis summary')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.path):
        print(f"Error: {args.path} is not a directory")
        return 1
    
    analyzer = ClassAnalyzer()
    analyzer.analyze_directory(args.path)
    
    analyzer.save_plantuml_diagram(
        filename=args.output,
        include_attributes=not args.no_attributes,
        include_methods=not args.no_methods
    )
    
    if args.summary:
        analyzer.print_analysis_summary()
    
    return 0

if __name__ == '__main__':
    exit(main()) 