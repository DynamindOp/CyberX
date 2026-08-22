#!/usr/bin/env python3
#Author: DynamindOP

import os
import sys
import re
import json
import math
from fractions import Fraction
from datetime import datetime


VERSION = "1.3.0"

VARIABLE_FILE = os.path.expanduser(
    "~/.pyculator_variables.json"
)

HISTORY_FILE = os.path.expanduser(
    "~/.pyculator_history"
)


# ============================================================
# COLORS
# ============================================================

RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
GRAY = "\033[90m"


# ============================================================
# UI
# ============================================================

def clear_screen():
    os.system(
        "cls" if os.name == "nt" else "clear"
    )


def banner():
    print(f"""
{CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                    PYCULATOR v{VERSION:<27}║
║                                                              ║
║                 MATHEMATICAL LANGUAGE                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{RESET}
""")


def error(message):
    print(
        f"{RED}✗ {message}{RESET}"
    )


def success(message):
    print(
        f"{GREEN}✓ {message}{RESET}"
    )


def result_output(value):
    print(
        f"{GREEN}→ {format_value(value)}{RESET}"
    )


# ============================================================
# DATA TYPES
# ============================================================

class Quantity:

    def __init__(self, value, unit):
        self.value = value
        self.unit = unit


class Symbolic:

    def __init__(
        self,
        terms=None,
        constant=0
    ):
        self.terms = terms or {}
        self.constant = constant
        self.clean()

    def clean(self):

        self.terms = {
            name: coefficient
            for name, coefficient
            in self.terms.items()
            if coefficient != 0
        }

        return self


# ============================================================
# FORMAT
# ============================================================

def is_number(value):

    return isinstance(
        value,
        (int, float, Fraction)
    )


def unwrap(value):

    if isinstance(value, Quantity):
        return value.value

    return value


def format_number(value):

    if isinstance(value, Fraction):

        if value.denominator == 1:
            return str(value.numerator)

        return (
            f"{value.numerator}/"
            f"{value.denominator}"
        )

    if isinstance(value, float):

        if value.is_integer():
            return str(int(value))

        return f"{value:.12g}"

    return str(value)


def format_value(value):

    if isinstance(value, Quantity):

        return (
            f"{format_number(value.value)}"
            f"({value.unit})"
        )

    if isinstance(value, Symbolic):

        parts = []

        for name, coefficient in (
            value.terms.items()
        ):

            if coefficient == 1:
                term = name

            elif coefficient == -1:
                term = "-" + name

            else:
                term = (
                    f"{format_number(coefficient)}"
                    f"{name}"
                )

            parts.append(term)

        if value.constant != 0:

            parts.append(
                format_number(
                    value.constant
                )
            )

        if not parts:
            return "0"

        output = parts[0]

        for part in parts[1:]:

            if part.startswith("-"):

                output += (
                    " - "
                    + part[1:]
                )

            else:

                output += (
                    " + "
                    + part
                )

        return output

    if isinstance(value, bool):

        return (
            "TRUE"
            if value
            else "FALSE"
        )

    return format_number(value)


# ============================================================
# SYMBOLIC OPERATIONS
# ============================================================

def make_symbol(name):

    return Symbolic(
        {name: 1}
    )


def symbolic_add(a, b):

    if not isinstance(a, Symbolic):
        a = Symbolic(constant=a)

    if not isinstance(b, Symbolic):
        b = Symbolic(constant=b)

    terms = dict(a.terms)

    for name, coefficient in b.terms.items():

        terms[name] = (
            terms.get(name, 0)
            + coefficient
        )

    return Symbolic(
        terms,
        a.constant + b.constant
    )


def symbolic_subtract(a, b):

    if not isinstance(a, Symbolic):
        a = Symbolic(constant=a)

    if not isinstance(b, Symbolic):
        b = Symbolic(constant=b)

    terms = dict(a.terms)

    for name, coefficient in b.terms.items():

        terms[name] = (
            terms.get(name, 0)
            - coefficient
        )

    return Symbolic(
        terms,
        a.constant - b.constant
    )


def symbolic_multiply(
    symbolic,
    number
):

    return Symbolic(
        {
            name:
            coefficient * number
            for name, coefficient
            in symbolic.terms.items()
        },
        symbolic.constant * number
    )


# ============================================================
# OPERATIONS
# ============================================================

def op_add(a, b):

    if isinstance(a, str) or isinstance(b, str):

        return (
            format_value(a)
            +
            format_value(b)
        )

    if isinstance(a, Symbolic) or isinstance(b, Symbolic):

        return symbolic_add(a, b)

    if isinstance(a, Quantity) and isinstance(b, Quantity):

        if a.unit != b.unit:
            raise ValueError(
                "Units must match."
            )

        return Quantity(
            a.value + b.value,
            a.unit
        )

    if isinstance(a, Quantity):

        return Quantity(
            a.value + unwrap(b),
            a.unit
        )

    if isinstance(b, Quantity):

        return Quantity(
            unwrap(a) + b.value,
            b.unit
        )

    return a + b


def op_subtract(a, b):

    if isinstance(a, Symbolic) or isinstance(b, Symbolic):

        return symbolic_subtract(a, b)

    if isinstance(a, Quantity) and isinstance(b, Quantity):

        if a.unit != b.unit:
            raise ValueError(
                "Units must match."
            )

        return Quantity(
            a.value - b.value,
            a.unit
        )

    if isinstance(a, Quantity):

        return Quantity(
            a.value - unwrap(b),
            a.unit
        )

    return unwrap(a) - unwrap(b)


def op_multiply(a, b):

    if isinstance(a, Symbolic):

        if not is_number(unwrap(b)):
            raise ValueError(
                "Symbolic multiplication "
                "requires a number."
            )

        return symbolic_multiply(
            a,
            unwrap(b)
        )

    if isinstance(b, Symbolic):

        if not is_number(unwrap(a)):
            raise ValueError(
                "Symbolic multiplication "
                "requires a number."
            )

        return symbolic_multiply(
            b,
            unwrap(a)
        )

    if isinstance(a, Quantity):

        return Quantity(
            a.value * unwrap(b),
            a.unit
        )

    if isinstance(b, Quantity):

        return Quantity(
            unwrap(a) * b.value,
            b.unit
        )

    return unwrap(a) * unwrap(b)


def op_divide(a, b):

    denominator = unwrap(b)

    if denominator == 0:
        raise ValueError(
            "Division by zero."
        )

    return unwrap(a) / denominator


def op_floor_divide(a, b):

    denominator = unwrap(b)

    if denominator == 0:
        raise ValueError(
            "Division by zero."
        )

    return math.floor(
        unwrap(a) / denominator
    )


def op_power(a, b):

    if isinstance(a, Symbolic):

        raise ValueError(
            "Symbolic powers are not supported."
        )

    return unwrap(a) ** unwrap(b)


def op_percentage(maximum, scored):

    maximum = unwrap(maximum)
    scored = unwrap(scored)

    if maximum == 0:
        raise ValueError(
            "Maximum cannot be zero."
        )

    return (
        f"{format_number(
            scored / maximum * 100
        )}%"
    )


def op_concat(a, b):

    return (
        format_value(a)
        +
        format_value(b)
    )


def op_absolute(value):

    if isinstance(value, Symbolic):

        raise ValueError(
            "Absolute value of a variable "
            "is not supported."
        )

    if isinstance(value, Quantity):

        return Quantity(
            abs(value.value),
            value.unit
        )

    return abs(
        unwrap(value)
    )


# ============================================================
# TOKENIZER
# ============================================================

TOKEN_REGEX = re.compile(
    r"""
    \s*
    (
        \d+(?:\.\d+)?
        |
        "(?:\\.|[^"])*"
        |
        [A-Za-z_][A-Za-z0-9_]*
        |
        >=
        |
        <=
        |
        !=
        |
        ==
        |
        \?=
        |
        [+\-*/^%&~(),{}\[\]<>?|=]
    )
    """,
    re.VERBOSE
)


def tokenize(text):

    tokens = []
    position = 0

    while position < len(text):

        match = TOKEN_REGEX.match(
            text,
            position
        )

        if not match:

            raise ValueError(
                "Unexpected character: "
                f"{text[position]}"
            )

        tokens.append(
            match.group(1)
        )

        position = match.end()

    return tokens


# ============================================================
# PARSER
# ============================================================

class Parser:

    def __init__(
        self,
        tokens,
        variables
    ):

        self.tokens = tokens
        self.variables = variables
        self.position = 0

    def current(self):

        if self.position >= len(self.tokens):
            return None

        return self.tokens[
            self.position
        ]

    def peek(self, offset=1):

        index = (
            self.position
            + offset
        )

        if index >= len(self.tokens):
            return None

        return self.tokens[index]

    def eat(self, expected=None):

        token = self.current()

        if token is None:
            raise ValueError(
                "Unexpected end of expression."
            )

        if (
            expected is not None
            and token != expected
        ):

            raise ValueError(
                f"Expected '{expected}', "
                f"got '{token}'."
            )

        self.position += 1

        return token

    def parse(self):

        value = self.comparison()

        if self.current() is not None:

            raise ValueError(
                "Unexpected token "
                f"'{self.current()}'."
            )

        return value

    def comparison(self):

        left = self.addition()

        operator = self.current()

        if operator in (
            ">",
            "<",
            ">=",
            "<=",
            "!=",
            "=",
            "?"
        ):

            self.eat()

            right = self.addition()

            a = unwrap(left)
            b = unwrap(right)

            if operator == ">":
                return a > b

            if operator == "<":
                return a < b

            if operator == ">=":
                return a >= b

            if operator == "<=":
                return a <= b

            if operator == "!=":
                return a != b

            if operator == "=":
                return a == b

            if operator == "?":

                if a > b:
                    return (
                        f"{format_value(a)} "
                        f"is greater than "
                        f"{format_value(b)}"
                    )

                if a < b:
                    return (
                        f"{format_value(a)} "
                        f"is smaller than "
                        f"{format_value(b)}"
                    )

                return (
                    f"{format_value(a)} "
                    f"is equal to "
                    f"{format_value(b)}"
                )

        if operator == "?=":

            self.eat("?=")

            right = self.addition()

            if unwrap(right) != 2:

                raise ValueError(
                    "Use ?=2 for even/odd."
                )

            number = unwrap(left)

            if not is_number(number):

                raise ValueError(
                    "Even/odd requires a number."
                )

            return (
                f"{format_value(number)} is "
                f"{'EVEN' if int(number) % 2 == 0 else 'ODD'}"
            )

        return left

    def addition(self):

        value = self.multiplication()

        while self.current() in (
            "+",
            "-"
        ):

            operator = self.eat()

            right = self.multiplication()

            if operator == "+":

                value = op_add(
                    value,
                    right
                )

            else:

                value = op_subtract(
                    value,
                    right
                )

        return value

    def multiplication(self):

        value = self.power()

        while self.current() in (
            "*",
            "/",
            "^",
            "%",
            "&"
        ):

            operator = self.eat()

            right = self.power()

            if operator == "*":

                value = op_multiply(
                    value,
                    right
                )

            elif operator == "/":

                value = op_divide(
                    value,
                    right
                )

            elif operator == "^":

                value = op_floor_divide(
                    value,
                    right
                )

            elif operator == "%":

                value = op_percentage(
                    value,
                    right
                )

            elif operator == "&":

                value = op_concat(
                    value,
                    right
                )

        while True:

            token = self.current()

            if token is None:
                break

            if token in (
                "(",
                "[",
                "{",
                "|"
            ):

                right = self.power()

                value = op_multiply(
                    value,
                    right
                )

                continue

            if re.fullmatch(
                r"[A-Za-z_][A-Za-z0-9_]*",
                token
            ):

                right = self.power()

                value = op_multiply(
                    value,
                    right
                )

                continue

            break

        return value

    def power(self):

        value = self.unary()

        if self.current() == "~":

            self.eat("~")

            exponent = self.power()

            value = op_power(
                value,
                exponent
            )

        return value

    def unary(self):

        if self.current() == "+":

            self.eat("+")
            return self.unary()

        if self.current() == "-":

            self.eat("-")

            value = self.unary()

            if isinstance(
                value,
                Symbolic
            ):

                return symbolic_multiply(
                    value,
                    -1
                )

            return -unwrap(value)

        return self.primary()

    def primary(self):

        token = self.current()

        if token is None:

            raise ValueError(
                "Expected a value."
            )

        if token in (
            "(",
            "[",
            "{"
        ):

            closing = {
                "(": ")",
                "[": "]",
                "{": "}"
            }[token]

            self.eat(token)

            value = self.addition()

            if self.current() != closing:

                raise ValueError(
                    f"Expected '{closing}' "
                    f"before "
                    f"'{self.current()}'."
                )

            self.eat(closing)

            return value

        if token == "|":

            self.eat("|")

            value = self.addition()

            if self.current() != "|":

                raise ValueError(
                    "Expected closing '|' "
                    "for absolute value."
                )

            self.eat("|")

            return op_absolute(value)

        if re.fullmatch(
            r"\d+(?:\.\d+)?",
            token
        ):

            self.eat()

            if "." in token:
                value = float(token)
            else:
                value = int(token)

            if self.current() == "(":

                self.eat("(")

                unit = self.eat()

                if self.current() != ")":

                    raise ValueError(
                        "Expected ')' after unit."
                    )

                self.eat(")")

                value = Quantity(
                    value,
                    unit
                )

            return value

        if token.startswith('"'):

            self.eat()

            return token[1:-1]

        if re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*",
            token
        ):

            self.eat()

            if token == "pi":
                return math.pi

            if token == "e":
                return math.e

            if token in self.variables:

                return self.variables[token]

            return make_symbol(token)

        raise ValueError(
            f"Unexpected token '{token}'."
        )


# ============================================================
# VARIABLES
# ============================================================

def load_variables():

    if not os.path.exists(
        VARIABLE_FILE
    ):
        return {}

    try:

        with open(
            VARIABLE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return {}


def save_variables(
    variables
):

    with open(
        VARIABLE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            variables,
            file,
            indent=2
        )


def define_permanent_variable(
    text,
    variables
):

    match = re.fullmatch(
        r"\s*"
        r"([A-Za-z_][A-Za-z0-9_]*)"
        r"\s*==\s*"
        r"(.+)"
        r"\s*",
        text
    )

    if not match:

        return None

    name = match.group(1)
    expression = match.group(2)

    value = evaluate(
        expression,
        variables
    )

    if isinstance(
        value,
        Symbolic
    ):

        raise ValueError(
            "Permanent variables "
            "must have a numeric value."
        )

    value = unwrap(value)

    variables[name] = value

    save_variables(
        variables
    )

    success(
        f"Permanent variable "
        f"'{name}' = {format_value(value)}"
    )

    return value


def split_temporary_variables(
    text
):

    parts = [
        part.strip()
        for part in text.split(",")
    ]

    if len(parts) == 1:

        return text, {}

    expression = parts[0]

    temporary = {}

    for part in parts[1:]:

        match = re.fullmatch(
            r"([A-Za-z_][A-Za-z0-9_]*)"
            r"\s*=\s*(.+)",
            part
        )

        if not match:

            raise ValueError(
                f"Invalid temporary "
                f"assignment: {part}"
            )

        name = match.group(1)
        value_text = match.group(2)

        value = evaluate(
            value_text,
            {}
        )

        if isinstance(
            value,
            Symbolic
        ):

            raise ValueError(
                "Variable value must "
                "be numeric."
            )

        temporary[name] = value

    return expression, temporary


# ============================================================
# EQUATION SOLVER
# ============================================================

def solve_for_x(
    text,
    variables
):

    match = re.fullmatch(
        r"\s*(.+?)"
        r"\s*=\s*"
        r"(.+?)"
        r"\s*,\s*x==\s*",
        text
    )

    if not match:

        return None

    left = match.group(1)
    right = match.group(2)

    def calculate(
        expression,
        x_value
    ):

        local = dict(
            variables
        )

        local["x"] = x_value

        value = evaluate(
            expression,
            local
        )

        if isinstance(
            value,
            Symbolic
        ):

            coefficient = (
                value.terms.get(
                    "x",
                    0
                )
            )

            return (
                coefficient * x_value
                +
                value.constant
            )

        return unwrap(value)

    left0 = calculate(
        left,
        0
    )

    left1 = calculate(
        left,
        1
    )

    right0 = calculate(
        right,
        0
    )

    right1 = calculate(
        right,
        1
    )

    left_coefficient = (
        left1 - left0
    )

    right_coefficient = (
        right1 - right0
    )

    coefficient = (
        left_coefficient
        -
        right_coefficient
    )

    constant = (
        right0 - left0
    )

    if coefficient == 0:

        if constant == 0:
            return "INFINITE SOLUTIONS"

        return "NO SOLUTION"

    answer = (
        constant / coefficient
    )

    return (
        f"x = {format_number(answer)}"
    )


# ============================================================
# FRACTIONS
# ============================================================

def fraction_command(
    text
):

    match = re.fullmatch(
        r"\s*"
        r"(-?\d+)"
        r","
        r"(\d+)"
        r"/"
        r"(\d+)"
        r"=="
        r"\s*",
        text
    )

    if match:

        whole = int(
            match.group(1)
        )

        numerator = int(
            match.group(2)
        )

        denominator = int(
            match.group(3)
        )

        if denominator == 0:

            raise ValueError(
                "Denominator cannot be zero."
            )

        sign = (
            -1
            if whole < 0
            else 1
        )

        numerator = (
            abs(whole)
            * denominator
            +
            numerator
        )

        fraction = Fraction(
            numerator * sign,
            denominator
        )

        return (
            f"{fraction.numerator}/"
            f"{fraction.denominator}"
        )

    match = re.fullmatch(
        r"\s*"
        r"(-?\d+)"
        r"/"
        r"(\d+)"
        r"=="
        r"\s*",
        text
    )

    if match:

        numerator = int(
            match.group(1)
        )

        denominator = int(
            match.group(2)
        )

        if denominator == 0:

            raise ValueError(
                "Denominator cannot be zero."
            )

        negative = numerator < 0

        numerator = abs(
            numerator
        )

        whole = (
            numerator
            // denominator
        )

        remainder = (
            numerator
            % denominator
        )

        if remainder == 0:

            return str(
                -whole
                if negative
                else whole
            )

        sign = "-" if negative else ""

        return (
            f"{sign}{whole},"
            f"{remainder}/{denominator}"
        )

    return None


# ============================================================
# EVALUATION
# ============================================================

def evaluate(
    text,
    variables
):

    text = text.strip()

    permanent = (
        define_permanent_variable(
            text,
            variables
        )
    )

    if permanent is not None:
        return permanent

    equation = solve_for_x(
        text,
        variables
    )

    if equation is not None:
        return equation

    fraction = fraction_command(
        text
    )

    if fraction is not None:
        return fraction

    expression, temporary = (
        split_temporary_variables(
            text
        )
    )

    local_variables = dict(
        variables
    )

    local_variables.update(
        temporary
    )

    tokens = tokenize(
        expression
    )

    parser = Parser(
        tokens,
        local_variables
    )

    return parser.parse()


# ============================================================
# HISTORY
# ============================================================

def save_history(
    expression,
    result
):

    try:

        with open(
            HISTORY_FILE,
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                json.dumps({
                    "time":
                        datetime.now().isoformat(),
                    "expression":
                        expression,
                    "result":
                        format_value(result)
                })
                + "\n"
            )

    except Exception:
        pass


def show_history():

    if not os.path.exists(
        HISTORY_FILE
    ):

        print(
            "No history."
        )

        return

    with open(
        HISTORY_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        lines = file.readlines()

    print(
        f"""
{CYAN}╔══════════════════════════════════════════════════════════════╗
║                    PYCULATOR HISTORY                         ║
╚══════════════════════════════════════════════════════════════╝{RESET}
"""
    )

    for line in lines[-50:]:

        try:

            item = json.loads(
                line
            )

            print(
                f"{item['expression']} "
                f"→ {item['result']}"
            )

        except Exception:
            pass


# ============================================================
# VARIABLES COMMANDS
# ============================================================

def show_variables(
    variables
):

    print(
        f"""
{CYAN}╔══════════════════════════════════════════════════════════════╗
║                    STORED VARIABLES                          ║
╠══════════════════════════════════════════════════════════════╣{RESET}
"""
    )

    if not variables:

        print(
            f"{CYAN}║  No permanent variables.                                   ║{RESET}"
        )

    else:

        for name, value in variables.items():

            line = (
                f"║  {name} = "
                f"{format_number(value)}"
            )

            print(
                f"{line:<62}{CYAN}║{RESET}"
            )

    print(
        f"{CYAN}╚══════════════════════════════════════════════════════════════╝{RESET}"
    )


def clear_variables(
    variables
):

    variables.clear()

    if os.path.exists(
        VARIABLE_FILE
    ):

        os.remove(
            VARIABLE_FILE
        )

    success(
        "All permanent variables have been cleared."
    )


def clear_specific_variable(
    variables,
    name
):

    if name not in variables:

        error(
            f"Permanent variable "
            f"'{name}' does not exist."
        )

        return

    del variables[name]

    save_variables(
        variables
    )

    success(
        f"Permanent variable "
        f"'{name}' has been cleared."
    )


# ============================================================
# HELP
# ============================================================

def help_menu():

    print(
        f"""
{CYAN}╔══════════════════════════════════════════════════════════════╗
║                    PYCULATOR HELP                            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║ OPERATORS                                                    ║
║                                                              ║
║  +       Addition                                            ║
║  -       Subtraction                                         ║
║  *       Multiplication                                      ║
║  /       Division                                            ║
║  ^       Floor division                                      ║
║  %       Percentage: MAX%SCORED                              ║
║  &       Concatenation                                       ║
║  ~       Power                                               ║
║                                                              ║
║ GROUPING                                                      ║
║                                                              ║
║  ( )     Parentheses                                         ║
║  [ ]     Brackets                                            ║
║  {{ }}    Braces                                              ║
║  | |     Absolute value                                      ║
║                                                              ║
║ COMPARISON                                                    ║
║                                                              ║
║  >       Greater than                                        ║
║  <       Less than                                           ║
║  >=      Greater/equal                                       ║
║  <=      Less/equal                                          ║
║  !=      Not equal                                           ║
║  ?       Compare                                             ║
║  ?=2     Even / odd                                          ║
║                                                              ║
║ VARIABLES                                                     ║
║                                                              ║
║  2x+5x                   Symbolic expression                 ║
║  2x+3,x=5                Temporary x                         ║
║  x==5                    Permanent x                         ║
║                                                              ║
║ EQUATIONS                                                     ║
║                                                              ║
║  4x-2=4,x==              Solve for x                         ║
║                                                              ║
║ FRACTIONS                                                     ║
║                                                              ║
║  6/5==                   Improper → mixed                    ║
║  1,1/5==                 Mixed → improper                    ║
║                                                              ║
║ UNITS                                                         ║
║                                                              ║
║  1(a)+2(a)               Unit arithmetic                     ║
║                                                              ║
║ VARIABLE COMMANDS                                             ║
║                                                              ║
║  vars                    Show permanent variables            ║
║  clearvar x              Delete only x                       ║
║  clearvars               Delete ALL permanent variables      ║
║                                                              ║
║ OTHER COMMANDS                                                ║
║                                                              ║
║  history                 Calculation history                 ║
║  clear                   Clear screen                        ║
║  examples                Show examples                       ║
║  version                 Version information                  ║
║  exit                    Exit Pyculator                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{RESET}
"""
    )


# ============================================================
# EXAMPLES
# ============================================================

def examples():

    print(
        f"""
{CYAN}╔══════════════════════════════════════════════════════════════╗
║                    PYCULATOR EXAMPLES                        ║
╚══════════════════════════════════════════════════════════════╝{RESET}

Basic:

  2+5
  10-4
  5*8
  20/4

Parentheses:

  (5-2)
  [5-2]
  {{5-2}}
  (2+3)*4

Absolute value:

  |5-8|
  |(5-8)+2|

Power:

  2~4

Floor division:

  9^2

Percentage:

  500%450

Concatenation:

  12&34
  10&20

Temporary variable:

  2x+3,x=5

Permanent variable:

  x==5

Then:

  2x+3

Show variables:

  vars

Delete one:

  clearvar x

Delete all:

  clearvars

Equation:

  4x-2=4,x==

Comparison:

  4>3
  4<3
  4?5

Even / odd:

  4?=2
  5?=2

Fractions:

  6/5==
  1,1/5==

Units:

  1(a)+2(a)
"""
    )


# ============================================================
# INTERACTIVE MODE
# ============================================================

def interactive():

    clear_screen()

    banner()

    print(
        f"{GRAY}"
        "Type 'help' for available operations."
        f"{RESET}\n"
    )

    variables = load_variables()

    while True:

        try:

            text = input(
                f"{CYAN}PYCULATOR ❯ {RESET}"
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print()
            break

        if not text:
            continue

        command = text.lower()

        if command == "exit":
            break

        if command == "help":
            help_menu()
            continue

        if command == "examples":
            examples()
            continue

        if command == "vars":
            show_variables(
                variables
            )
            continue

        if command == "clearvars":

            clear_variables(
                variables
            )

            continue

        if command.startswith(
            "clearvar "
        ):

            name = text[
                len("clearvar "):
            ].strip()

            if not re.fullmatch(
                r"[A-Za-z_][A-Za-z0-9_]*",
                name
            ):

                error(
                    "Invalid variable name."
                )

                continue

            clear_specific_variable(
                variables,
                name
            )

            continue

        if command == "history":
            show_history()
            continue

        if command == "clear":

            clear_screen()
            banner()

            continue

        if command == "version":

            print(
                f"PYCULATOR v{VERSION}"
            )

            continue

        try:

            result = evaluate(
                text,
                variables
            )

            result_output(
                result
            )

            save_history(
                text,
                result
            )

        except Exception as exc:

            error(
                str(exc)
            )


# ============================================================
# COMMAND-LINE MODE
# ============================================================

def main():

    if len(sys.argv) == 1:

        interactive()

        return

    expression = " ".join(
        sys.argv[1:]
    )

    command = expression.lower()

    if command == "help":

        help_menu()
        return

    if command == "examples":

        examples()
        return

    variables = load_variables()

    if command == "clearvars":

        clear_variables(
            variables
        )

        return

    if command.startswith(
        "clearvar "
    ):

        name = expression[
            len("clearvar "):
        ].strip()

        if not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*",
            name
        ):

            error(
                "Invalid variable name."
            )

            return

        clear_specific_variable(
            variables,
            name
        )

        return

    try:

        result = evaluate(
            expression,
            variables
        )

        print(
            format_value(result)
        )

        save_history(
            expression,
            result
        )

    except Exception as exc:

        error(
            str(exc)
        )


if __name__ == "__main__":

    main()
