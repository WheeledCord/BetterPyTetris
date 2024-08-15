import re

def convert_to_python(expr):
    expr = expr.replace('\\left(', '(').replace('\\right)', ')')
    expr = re.sub(r'\\frac{([^{}]+)}{([^{}]+)}', r'(\1)/(\2)', expr).replace('\\frac','')
    expr = expr.replace('{', '(').replace('}', ')')
    expr = expr.replace('^', '**')  # Replace exponentiation
    
    return expr.strip()

def flatten_functions(functions):
    # Create a dictionary to hold the functions
    function_dict = {}
    
    # Function to replace variables with their expressions
    def replace_vars(expr):
        for var, repl in function_dict.items():
            if var != 'y':
                expr = expr.replace(var, f'({repl})')
        return expr

    # Extract function definitions into the dictionary
    for func in functions:
        match = re.match(r'(\w+)=([\s\S]+)', func)
        if match:
            var, expr = match.groups()
            # Convert LaTeX-like expressions to Python-compatible expressions
            function_dict[var] = convert_to_python(expr)
    for var, repl in function_dict.items():
        function_dict[var] = replace_vars(repl)

    # Assume the last function in the list is the main y= function
    flattened_expr = function_dict['y']
    return f'y={flattened_expr}'

# Example usage
functions = [
    'T=60',
    'O=10',
    'M=10',
    'm=1',
    'B=1',
    'u=(x-\\left(\\frac{\\frac{T}{O}}{2}\\right))/(\\left(T-\\frac{\\frac{T}{O}}{2}\\right)-\\left(\\frac{\\frac{T}{O}}{2}\\right))',
    'F=(1-u)^{2}*M+2*(1-u)*u*B+u^{2}*m',
    'y=F*\\sin\\left(\\frac{2\\cdot\\pi\\cdot\\left(0.5O\\right)\\cdot x}{T}\\right)'
]
flattened = flatten_functions(functions)
print(flattened)