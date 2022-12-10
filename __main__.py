"""
Source code for the EPL Interpreter.

Usage:
    epl  /path/to/guimpy filepath.EPL
"""


from __future__ import annotations
import sys, os, ast, subprocess, platform, shutil, copy, json, textwrap, warnings
from typing import Any, Iterable


line_number = 1
variables = {}
operators = ['+', '-', '/', '*', '^']
special_vars = {'file': 'string'}
if_STMTS = {}
if_STMT = {}
directory = os.path.dirname(__file__)
if directory.endswith('.'):
    directory = directory[:-1]
    if directory.endswith('/'):
        directory = directory[:-1]
quotes = ["'", '"']
operating_system = platform.system()
allowed = 'qwertyuiopasdfghjklzxcvbnm_QWERTYUIOPASDFGHJJKLZXCVBNNM1234567890 '
all_allowed_chars = allowed + '''.()'"{}[]'''
old_list = list
with open(f'{directory}/log.txt', 'w'):
    pass


def verbose(b: bool):
    with open(f'{directory}/isverbose.txt', 'w') as verbose_file:
        verbose_file.write(f'{b}')
        
        
def isverbose():
    with open(f'{directory}/isverbose.txt') as verbose_file:
        b = verbose_file.read()
    if b == 'True':
        return True
    elif b == 'False':
        return False


def p(*values, seperator: str=' ', end='\n', flush=False, file=None):
    if not isverbose():
        return
    print(*values, sep=seperator, end=end, flush=flush, file=file)
    with open(f'{directory}/log.txt', 'a') as log_file:
        log_file.write(seperator.join(values) + end)
        
        
def isallowed(string: str):
    for letter in string:
        if letter not in allowed:
            return False
    return True


def run_use(string: str):
    path = string[1:-1]
    if string[0] in quotes and string[-1] in quotes:
        if not os.path.exists(path):
            Moduleerror(line_number, special_vars['file'], f'EPL File "{path}" does not exist.')
        if not os.path.isfile(path):
            if path.endswith('/'):
                path += 'main.epl'
            else:
                path += '/main.epl'
        with open(string[1:-1]) as module:
            code = module.read().splitlines()
        for line in code:
            parse(line)
    elif not string[0].isdigit() and isallowed(string[1:]):
        path = f'"{directory}/libraries/{string[1:]}"'
        if not os.path.exists(path[1:-1]):
            Moduleerror(line_number, special_vars['file'], f'Unknown module "{path}".')
        if os.path.isdir(path[1:-1]):
            path = path[:-1]
            path += '/main.epl"'
            if not os.path.exists(path[1:-1]):
                Moduleerror(line_number, special_vars['file'], f'Unknown module "{path}".')
        run_use(path)
    elif not string[0].isdigit() and isallowed(string[1:].replace('.', '')):
        path = f'"{directory}/libraries/{string[1:].replace(".", "")}/main.epl"'
        run_use(path)
    elif string[0].isdigit() or not isallowed(string[1:]):
        Syntaxerror(line_number, special_vars['file'], f'Name "{string}" for use statement is not allowed.')


def command(string: str):
    args = string.split()
    return subprocess.run(args, capture_output=True, text=True)


class Error:
    def __init__(self, error_dict: dict, exit_interpreter: bool=True) -> None:
        self.error_list = error_dict
        p(f"File \"{error_dict['file']}\", line {error_dict['line']}:\n\t{__class__.__name__}: {error_dict['message']}")
        if exit_interpreter:
            raise SystemExit()
    
    
class Syntaxerror(Error):
    def __init__(self, line_number: int, file: str, message: str) -> None:
        super().__init__({'line': line_number, 'file': file, 'message': message}, True)
        
        
class Moduleerror(Error):
    def __init__(self, line_number: int, file: str, message: str) -> None:
        super().__init__({'line': line_number, 'file': file, 'message': message}, True)
        

class Characteristicerror(Error):
    def __init__(self, line_number: int, file: str, message: str) -> None:
        super().__init__({'line': line_number, 'file': file, 'message': message}, True)


class ArgError(Exception):
    pass


def get_indented_code(full_code: str, start: int, expr_trying: str='expression'):
    lines = full_code.splitlines()[start:]
    indented_code = ''
    for index, line in enumerate(lines):
        if line.startswith(' '):
            indented_code += f'{line}\n'
        else:
            return indented_code
    Syntaxerror(special_vars['file'], line_number, f'Nothing after {expr_trying}.')


def gfindex(iterable: Iterable, index: int):
    try:
        return iterable[index]
    except IndexError:
        return


help_message = '''
EPL Language CLI.

If no args, run interactive mode.
Usage:
    -h, --h, --help, -help   -> Prints this message
    install, download, i, d  -> Installs github repository (using format <github-author>/<github-repo>) acting as a module and configuring it
    Unknown Arg              -> Used as filename
'''


def is_number(string: str):
    try:
        float(string)
        return True
    except ValueError:
        return False
    
    
class EplClass:
    def __objectname__(self):
        return self.__class__.__name__
    
    
class number(int, EplClass):
    def __xor__(self, number: int) -> int:
        return self ** number
    


class decimal(float, EplClass):
    def __xor__(self, number: int) -> int:
        return self ** number
    
    
    def __truediv__(self, other):
        if isinstance(other, decimal):
            first = float(repr(self).rstrip('0'))
            second = float(repr(self).rstrip(0))
            firsts_decimal_places = len(repr(first)[repr(first).index('.'):])
            seconds_decimal_places = len(repr(second)[repr(second).index('.'):])
            first = int(repr(first).replace('.', ''))
            second = int(repr(second).replace('.', ''))
            whole_number_answer = str(first / second)
            print(whole_number_answer, 'a')
            decimal_number_answer = whole_number_answer[:firsts_decimal_places + seconds_decimal_places + 1] + '.' + whole_number_answer[firsts_decimal_places + seconds_decimal_places + 1:]
            return decimal(decimal_number_answer)
        else:
            super().__truediv__(other)


class text(str, EplClass):
    pass


class true:
    
    
    def __repr__(self) -> str:
        return 'true'
    
    
    def __bool__(self):
        return True


class false:
    
    
    def __repr__(self) -> str:
        return 'false'
    
    
    def __bool__(self):
        return False
    
    
class nothing(EplClass):
    def __init__(self) -> None:
        for attribute in dir(self):
            if attribute in ['__objectname__', '__repr__']:
                continue
            try:
                setattr(self, attribute, lambda: Characteristicerror(line_number, special_vars['file'], f'Unknown Characteristic "{attribute}".'))
            except (TypeError, AttributeError):
                continue
            
            
    def __repr__(self) -> str:
        return self.__objectname__()
    
    
class list(old_list):
    
    
    def append(self, __object: Any) -> None:
        raise AttributeError('Unknown Attribute "append".')
    

    def add(self, obj: Any, where: number | text='end') -> None:
        if where == 'end':
            super().append(obj)
        elif where == 'beginning':
            super().insert(0, obj)
        elif isinstance(where, int):
            super().insert(where - 1, obj)
    
    
    def __iadd__(self, new_item):
        self.add(new_item)
        
        
    def copy(self):
        return copy.deepcopy(self)
        
        
    def __add__(self, new_item):
        new_list = self.copy()
        new_list.add(new_item)
        return new_list
    
            
            
class negetive(int, EplClass):
    def __new__(cls, obj):
        if not str(obj)[0] == '-' and not str(obj).replace('.', '', 1).replace('-', '', 1).isdigit():
            Syntaxerror(line_number, special_vars['file'], 'Invalid negetive number.')
        return super().__new__(cls, obj)


def parse_attributes(string: str):
    string += ' -dummy "dummy text"'
    option_list = string.split()
    attribute = {}
    attributes = {}
    for option_index, option in enumerate(option_list):
        if option.startswith('-'):
            if is_number(option):
                attribute['value'] += option + ' '
            if attribute.get('value'):
                if attribute['name'] == 'gui':
                    attribute['value'] = ast.literal_eval(f'''"{attribute['value']}"''')
                else:
                    attribute['value'] = ast.literal_eval(attribute['value'])
                if isinstance(attribute['value'], str):
                    attribute['value'] = attribute['value'].replace('{[~]}', '-')
                attributes[attribute['name']] = attribute['value']
            attribute = {'name': option[1:], 'value': ''}
        else:
            if attribute:
                attribute['value'] += option + ' '
    return attributes


def expression(string: str):
    if not string:
        pass
    if any(['+' in string, '-' in string, '*' in string, '/' in string, '^' in string]):
        if any(['++' in string, '--' in string, '//' in string, '^^' in string]):
            Syntaxerror('No more than 1 plus, minus, or divide sign can be in expression.')
        expr = ''
        previous = ''
        for letter in string:
            if letter in operators:
                if previous in variables:
                    expr += repr(expression(previous))
                elif previous in all_allowed_chars:
                    expr += previous
                expr += letter
            elif letter in all_allowed_chars:
                expr += letter
        return eval(expr)
    elif string[0] in quotes and string[-1] in quotes:
        return text(string[1:-1])
    elif string[0] == ';' and string[-1] in quotes:
        return text(string[2:-1].format(**variables))
    elif string.startswith('-') and string.count('-') == 1:
        return negetive(string)
    elif string == 'nothing':
        return nothing()
    elif string in variables:
        return variables[string]
    elif string.startswith('read'):
        if string.startswith('read with prompt as'):
            return input(expression(string[20:]))
        else:
            return input()
    elif string.startswith('typename '):
        return expression(string[9:]).__objectname__()
    elif string == 'true':
        return true()
    elif string == 'false':
        return false()
    elif is_number(string):
        if string.isdigit():
            return number(string)
        if string.replace('.', '').isdigit() and string.count('.') == 1:
            return decimal(string)
        elif string.replace('.', '').isdigit() and string.count('.') > 1:
            Syntaxerror(special_vars['file'], line_number, 'More than 1 dot in decimal.')
    else:
        warnings.filterwarnings('ignore', category=SyntaxWarning)
        if eval(string, variables) == True:
            return true()
        else:
            return false()
            

def parse(string: str):
    global line_number, if_STMT
    # TODO: Create if statement
    splitted_text = string.split()
    if not string:
        line_number += 1
        return
    elif gfindex(splitted_text, 0) == 'write':
        print(expression(' '.join(splitted_text[1:])))
    elif isallowed(gfindex(splitted_text, 0)) and gfindex(splitted_text, 1) == 'is':
        variables[splitted_text[0]] = expression(' '.join(splitted_text[2:]))
    elif gfindex(splitted_text, 0) == 'use':
        run_use(string[3:])
    elif gfindex(splitted_text, 0) == 'read':
        if string.startswith('read with prompt as '):
            input(expression(string[20:]))
        else:
            input()
    elif string.startswith('!'):
        pass
    line_number += 1
    
    
def exit(code: int=0):
    raise SystemExit(code)


if __name__ == '__main__':
    if len(sys.argv[1:]) not in [0, 1, 2, 3, 4]:
        raise ArgError('Only 0-4 args allowed.')
    try:
        arg = sys.argv[1]
    except IndexError:
        while True:
            try:
                line = input('>>> ')
                if not line:
                    continue
                if line == 'exit':
                    break
                parse(line)
            except KeyboardInterrupt:
                break
        exit()
    if arg in ['-h', '-help', '--h', '--help']:
        p(help_message)
        exit()
    if arg in ['install', 'download', 'i', 'd']:
        p('Installing project into environment...')
        arg3 = sys.argv[2]
        if arg3 in ['-h', '-host']:
            p('SET HasHost -> true')
            git_repo = f'https://{sys.argv[3]}/{sys.argv[4]}'
            git_repo_name = sys.argv[4].split('/', 1)[1]
        else:
            p('SET HasHost -> false')
            git_repo = f'https://github.com/{sys.argv[2]}.git'
            git_repo_name = sys.argv[2].split('/', 1)[1]
            author = sys.argv[2].split('/', 1)[0]
        libraries_dir = f'{directory}/libraries'
        installed_project = f'{libraries_dir}/{git_repo_name}'
        p(f'SET Environment -> ("ProjectPath" -> "{installed_project}" "CurrentDirectory" -> "{libraries_dir}")')
        if os.path.isdir(f'{libraries_dir}/{git_repo_name}'):
            p('Already installed EPL module. Updating old module...')
            shutil.rmtree(f'{directory}/libraries/{git_repo_name}')
            os.system(f'python3 {directory} install {author}/{git_repo_name}')
            exit()
        with open(f'{directory}/gitlog.txt', 'w') as file:
            p('All info set, installing...')
            output = command(f'git clone {git_repo} {directory}/libraries/{git_repo_name}')
            p('Writing to log...')
            file.write(output.stderr)
            if output.returncode != 0:
                p(f'An error has occured. See {directory}/gitlog.txt for more details.')
        if os.path.exists(f'{libraries_dir}/{git_repo_name}/requires.txt'):
            p('Installing requirements...')
            with open(f'{libraries_dir}/{git_repo_name}/requires.txt') as requires_file:
                requirements = requires_file.read().splitlines()
            for requirement in requirements:
                if not requirement:
                    continue
                install_command = f'python3 {directory} install {requirement}'
                os.system(install_command)
        if not os.path.isdir(f'{installed_project}/{operating_system}'):
            if not os.path.isdir(f'{installed_project}/UnknownSystem'):
                print('Error: System -> Invalid system because there is no handler for it. Please switch systems to use this module.')
                shutil.rmtree(installed_project)
                exit()
            if os.path.exists(f'{installed_project}/UnknownSystem/on_install.epl') and os.path.isfile('{installed_project}/UnknownSystem/on_install.epl'):
                os.system(f'python3 {directory} {installed_project}/UnknownSystem/on_install.epl')
            operating_system = 'UnknownSystem'
        if os.path.isdir(f'{installed_project}/AnySystem'):
            for file in os.listdir(f'{installed_project}/AnySystem'):
                shutil.move(f'{installed_project}/AnySystem/{file}', f'{installed_project}/{operating_system}/{file}')
        os.system(f'python3 {directory} {installed_project}/{operating_system}/on_install.epl')
        shutil.copytree(f'{directory}/libraries/{git_repo_name}/{operating_system}', f'{git_repo_name}-c')
        if os.path.isfile(f'{installed_project}/module_info.json') and os.path.exists(f'{installed_project}/module_info.json'):
            metadata = json.load(open(f'{installed_project}/module_info.json'))
            epl_modules = json.load(open(f'{directory}/epl_modules.json'))
            epl_modules[git_repo_name] = metadata
            json.dump(epl_modules, open(f'{directory}/epl_modules.json'))
        shutil.rmtree(f'{directory}/libraries/{git_repo_name}')
        shutil.move(f'{directory}/{git_repo_name}-c', f'{directory}/libraries/{git_repo_name}')
        exit()
    if arg in ['uninstall', 'undownload', 'ui', 'ud']:
        p('Uninstalling module from environment...')
        epl_module = sys.argv[2].split('/')[2]
        module_path = f'{directory}/libraries/{epl_module}'
        if not os.path.exists(module_path):
            p(f'!ModuleError -> Unknown module "{epl_module}".')
            exit()
        shutil.rmtree(module_path)
        exit()
    if arg in ['-v', '-verbose']:
        b = sys.argv[2]
        if b not in ['true', 'false']:
            print(f'FatalError >> Expected true or false, got "{b}".')
            exit()
        if b == 'true':
            verbose(True)
        elif b == 'false':
            verbose(False)
        exit()
    special_vars['file'] = arg
    with open(arg) as file:
        lines = file.read().splitlines()
    gui = None
    for line in lines:
        parse(line)
