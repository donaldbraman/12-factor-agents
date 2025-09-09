#!/usr/bin/env python3
"""
CLI interface for the Dynamic Context Priming System.

Provides command-line access to primer functionality for rapid context generation.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from .dynamic_primer import DynamicContextPrimer


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from file or return defaults"""
    default_config = {
        "default_primer": "feature_development",
        "template_dir": "primers/templates",
        "output_dir": "output/primers",
        "auto_chain": False,
    }

    if config_path and config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                default_config.update(config)
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
            print("Using default configuration")

    return default_config


def create_primer_command(args):
    """Handle primer creation command"""
    primer = DynamicContextPrimer()

    # Parse variables from command line
    variables = {}
    if args.variables:
        for var in args.variables:
            if "=" in var:
                key, value = var.split("=", 1)
                variables[key] = value
            else:
                variables[var] = True

    # Load variables from JSON file if provided
    if args.variables_file:
        try:
            with open(args.variables_file, "r") as f:
                file_vars = json.load(f)
                variables.update(file_vars)
        except Exception as e:
            print(f"Error loading variables file: {e}")
            return 1

    try:
        # Generate primer
        result = primer.prime(args.primer_type, variables)

        # Output handling
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result.content)
            print(f"Primer written to: {output_path}")
        else:
            print(result.content)

        # Show performance metrics if requested
        if args.verbose:
            print(f"\nGeneration time: {result.generation_time:.4f}s")
            print(f"Template: {result.template_used}")
            print(f"Variables: {len(variables)} provided")

        return 0

    except Exception as e:
        print(f"Error generating primer: {e}")
        return 1


def list_primers_command(args):
    """Handle list primers command"""
    primer = DynamicContextPrimer()

    print("Available Primers:")
    print("==================")

    for name, func in primer.primer_registry.items():
        doc = func.__doc__ or "No description available"
        # Get first line of docstring
        description = doc.split("\n")[0].strip()
        print(f"  {name:<20} - {description}")

    if args.verbose:
        print("\nTemplate files:")
        template_dir = Path("primers/templates")
        if template_dir.exists():
            for template_file in template_dir.glob("*.md"):
                print(f"  {template_file.stem}")

    return 0


def validate_template_command(args):
    """Handle template validation command"""
    template_path = Path(args.template)

    if not template_path.exists():
        print(f"Template file not found: {template_path}")
        return 1

    try:
        from jinja2 import Template, meta, Environment

        # Read template content
        content = template_path.read_text()

        # Parse template
        env = Environment()
        template = env.parse(content)

        # Extract variables
        variables = meta.find_undeclared_variables(template)

        print(f"Template: {template_path}")
        print("=" * (10 + len(str(template_path))))

        if variables:
            print("Required variables:")
            for var in sorted(variables):
                print(f"  - {var}")
        else:
            print("No variables required")

        # Validate syntax
        try:
            Template(content)
            print("✓ Template syntax is valid")
        except Exception as e:
            print(f"✗ Template syntax error: {e}")
            return 1

        return 0

    except Exception as e:
        print(f"Error validating template: {e}")
        return 1


def interactive_command(args):
    """Handle interactive primer creation"""
    primer = DynamicContextPrimer()

    print("Interactive Primer Creation")
    print("==========================")

    # List available primers
    print("\nAvailable primers:")
    for i, (name, func) in enumerate(primer.primer_registry.items(), 1):
        doc = func.__doc__ or "No description"
        description = doc.split("\n")[0].strip()
        print(f"  {i}. {name} - {description}")

    # Get primer selection
    while True:
        try:
            selection = input("\nSelect primer (number or name): ").strip()

            # Try by number first
            if selection.isdigit():
                primer_names = list(primer.primer_registry.keys())
                idx = int(selection) - 1
                if 0 <= idx < len(primer_names):
                    primer_type = primer_names[idx]
                    break

            # Try by name
            if selection in primer.primer_registry:
                primer_type = selection
                break

            print("Invalid selection. Please try again.")

        except KeyboardInterrupt:
            print("\nCancelled.")
            return 1

    # Collect variables interactively
    print(f"\nConfiguring {primer_type} primer:")
    variables = {}

    # Get common variables
    common_vars = {
        "project_name": "Project name",
        "task_description": "Task description",
        "priority": "Priority (High/Medium/Low)",
        "complexity": "Complexity (High/Medium/Low)",
    }

    for var, prompt in common_vars.items():
        value = input(f"{prompt}: ").strip()
        if value:
            variables[var] = value

    # Generate primer
    try:
        result = primer.prime(primer_type, variables)

        # Show result
        print("\n" + "=" * 60)
        print("Generated Primer:")
        print("=" * 60)
        print(result.content)

        # Ask about saving
        save = input("\nSave to file? (y/N): ").strip().lower()
        if save in ["y", "yes"]:
            filename = input("Filename (default: primer.md): ").strip() or "primer.md"
            output_path = Path(filename)
            output_path.write_text(result.content)
            print(f"Saved to: {output_path}")

        return 0

    except Exception as e:
        print(f"Error generating primer: {e}")
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Dynamic Context Priming System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create feature_development -v task_description="Add user authentication"
  %(prog)s create bug_fix --variables-file vars.json -o bug_fix_primer.md
  %(prog)s list --verbose
  %(prog)s validate primers/templates/feature_development.md
  %(prog)s interactive
        """,
    )

    parser.add_argument("--config", type=Path, help="Configuration file path")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a primer")
    create_parser.add_argument("primer_type", help="Type of primer to create")
    create_parser.add_argument(
        "-v",
        "--variables",
        action="append",
        help="Variables in key=value format (can be used multiple times)",
    )
    create_parser.add_argument(
        "--variables-file", type=Path, help="JSON file containing variables"
    )
    create_parser.add_argument("-o", "--output", type=Path, help="Output file path")
    create_parser.add_argument(
        "--verbose", action="store_true", help="Show additional information"
    )
    create_parser.set_defaults(func=create_primer_command)

    # List command
    list_parser = subparsers.add_parser("list", help="List available primers")
    list_parser.add_argument(
        "--verbose", action="store_true", help="Show additional information"
    )
    list_parser.set_defaults(func=list_primers_command)

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a template")
    validate_parser.add_argument("template", help="Template file to validate")
    validate_parser.set_defaults(func=validate_template_command)

    # Interactive command
    interactive_parser = subparsers.add_parser(
        "interactive", help="Interactive primer creation"
    )
    interactive_parser.set_defaults(func=interactive_command)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Load configuration
    config = load_config(args.config)

    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
