#!/usr/bin/env python
"""
Script to generate automatic code documentation from docstrings.
"""
import os
import sys
import inspect
import importlib
import pkgutil
from pathlib import Path

def get_module_docstring(filepath):
    """
    Get the module-level docstring of a file.
    
    Args:
        filepath: The path to the Python file
        
    Returns:
        The docstring as a string, or None if no docstring is found
    """
    with open(filepath, "r", encoding="utf-8") as file:
        source = file.read()
    
    # Simple extraction of module docstring (between first triple quotes)
    if '"""' in source:
        start = source.find('"""') + 3
        end = source.find('"""', start)
        if end > start:
            return source[start:end].strip()
    
    return None

def get_package_modules(package_path, base_package):
    """
    Get all modules in a package.
    
    Args:
        package_path: The path to the package directory
        base_package: The import path for the base package
        
    Returns:
        A list of (module_name, module_path) tuples
    """
    modules = []
    
    for item in os.listdir(package_path):
        item_path = os.path.join(package_path, item)
        
        # Skip __pycache__ and hidden directories
        if item.startswith('__') or item.startswith('.'):
            continue
            
        # Handle Python modules
        if item.endswith('.py'):
            module_name = item[:-3]  # Remove .py extension
            module_path = f"{base_package}.{module_name}"
            modules.append((module_name, module_path))
            
        # Handle packages (directories with __init__.py)
        elif os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, '__init__.py')):
            package_name = item
            package_path = f"{base_package}.{package_name}"
            modules.append((package_name, package_path))
            # Recursively add modules from the package
            modules.extend(get_package_modules(item_path, package_path))
            
    return modules

def document_function(function):
    """
    Generate documentation for a function.
    
    Args:
        function: The function object to document
        
    Returns:
        A markdown string with the function documentation
    """
    docs = []
    
    # Function signature
    signature = str(inspect.signature(function))
    docs.append(f"### `{function.__name__}{signature}`\n")
    
    # Function docstring
    if function.__doc__:
        docs.append(function.__doc__.strip())
    
    docs.append("\n")
    return "\n".join(docs)

def document_class(cls):
    """
    Generate documentation for a class.
    
    Args:
        cls: The class object to document
        
    Returns:
        A markdown string with the class documentation
    """
    docs = []
    
    # Class name and bases
    bases = ', '.join(base.__name__ for base in cls.__bases__ if base.__name__ != 'object')
    if bases:
        docs.append(f"## Class: `{cls.__name__}` (inherits from: {bases})\n")
    else:
        docs.append(f"## Class: `{cls.__name__}`\n")
    
    # Class docstring
    if cls.__doc__:
        docs.append(cls.__doc__.strip())
        docs.append("\n")
    
    # Class methods
    method_docs = []
    for name, method in inspect.getmembers(cls, inspect.isfunction):
        # Skip private and special methods
        if name.startswith('_') and name != '__init__':
            continue
        
        method_docs.append(document_function(method))
    
    if method_docs:
        docs.append("### Methods\n")
        docs.extend(method_docs)
    
    return "\n".join(docs)

def document_module(module_path):
    """
    Generate documentation for a module.
    
    Args:
        module_path: The import path for the module
        
    Returns:
        A markdown string with the module documentation
    """
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        return f"Error importing module {module_path}: {e}\n"
    
    docs = []
    
    # Module name and docstring
    docs.append(f"# Module: `{module_path}`\n")
    
    if module.__doc__:
        docs.append(module.__doc__.strip())
        docs.append("\n")
    
    # Document classes
    class_docs = []
    for name, cls in inspect.getmembers(module, inspect.isclass):
        # Only document classes defined in this module
        if cls.__module__ == module_path:
            class_docs.append(document_class(cls))
    
    if class_docs:
        docs.append("# Classes\n")
        docs.extend(class_docs)
        docs.append("\n")
    
    # Document functions
    function_docs = []
    for name, function in inspect.getmembers(module, inspect.isfunction):
        # Only document functions defined in this module
        if function.__module__ == module_path:
            function_docs.append(document_function(function))
    
    if function_docs:
        docs.append("# Functions\n")
        docs.extend(function_docs)
    
    return "\n".join(docs)

def generate_documentation(app_path, output_dir):
    """
    Generate documentation for the entire application.
    
    Args:
        app_path: Path to the application directory
        output_dir: Directory to write documentation files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Document main app package
    packages = [
        ("api", "app.api"),
        ("core", "app.core"),
        ("db", "app.db"),
        ("middleware", "app.middleware"),
        ("models", "app.models"),
        ("schemas", "app.schemas"),
        ("services", "app.services"),
        ("tasks", "app.tasks"),
        ("utils", "app.utils")
    ]
    
    index_content = ["# Code Documentation\n", "## Packages\n"]
    
    for package_name, package_path in packages:
        package_dir = os.path.join(app_path, package_name)
        
        if not os.path.exists(package_dir):
            continue
            
        # Create package documentation directory
        package_doc_dir = os.path.join(output_dir, package_name)
        os.makedirs(package_doc_dir, exist_ok=True)
        
        index_content.append(f"- [{package_name}]({package_name}/README.md)")
        
        package_index = [f"# Package: {package_name}\n"]
        
        # Document package modules
        modules = get_package_modules(package_dir, f"app.{package_name}")
        for module_name, module_path in modules:
            # Generate documentation for the module
            module_doc = document_module(module_path)
            
            # Write module documentation to file
            module_filename = f"{module_name}.md"
            with open(os.path.join(package_doc_dir, module_filename), 'w', encoding='utf-8') as f:
                f.write(module_doc)
            
            # Add module to package index
            package_index.append(f"- [{module_name}]({module_filename})")
        
        # Write package index
        with open(os.path.join(package_doc_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write("\n".join(package_index))
    
    # Write main index
    with open(os.path.join(output_dir, "code_reference.md"), 'w', encoding='utf-8') as f:
        f.write("\n".join(index_content))

def main():
    """Main entry point for the script."""
    # Get the app directory path (relative to this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    app_dir = os.path.join(project_dir, 'app')
    
    # Output documentation to the docs/code directory
    output_dir = os.path.join(project_dir, 'docs', 'code')
    
    print(f"Generating documentation from {app_dir} to {output_dir}")
    generate_documentation(app_dir, output_dir)
    print("Documentation generation complete!")

if __name__ == "__main__":
    main() 