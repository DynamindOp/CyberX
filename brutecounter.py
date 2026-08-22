#!/usr/bin/env python3

import itertools
import string
import time
import os
import sys


# ============================================================
# SETTINGS
# ============================================================

BATCH_SIZE = 100_000
MAX_LENGTH = 16

# Common printable keyboard special characters
SPECIAL_CHARACTERS = r"""!@#$%^&*()-_=+[]{};:'",.<>/?\|`~"""


# ============================================================
# UI
# ============================================================

CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"


def clear_screen():
    os.system(
        "cls" if os.name == "nt" else "clear"
    )


def banner():

    print(
        f"""
{CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║             COMBINATION BRUTE COUNTER                        ║
║                                                              ║
║                  Python Edition                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{RESET}
"""
    )


def ask_yes_no(question):

    while True:

        answer = input(
            f"{question} [y/n]: "
        ).strip().lower()

        if answer in ("y", "yes"):
            return True

        if answer in ("n", "no"):
            return False

        print(
            f"{YELLOW}Please enter y or n.{RESET}"
        )


def get_number(prompt):

    while True:

        try:

            value = int(
                input(prompt).strip()
            )

            if value >= 0:
                return value

            print(
                f"{RED}Enter a number >= 0.{RESET}"
            )

        except ValueError:

            print(
                f"{RED}Enter a valid number.{RESET}"
            )


# ============================================================
# CHARACTER SET
# ============================================================

def build_charset():

    characters = ""

    if ask_yes_no(
        "Include numbers (0-9)?"
    ):
        characters += string.digits

    if ask_yes_no(
        "Include capital letters (A-Z)?"
    ):
        characters += string.ascii_uppercase

    if ask_yes_no(
        "Include small letters (a-z)?"
    ):
        characters += string.ascii_lowercase

    if ask_yes_no(
        "Include special keyboard characters?"
    ):
        characters += SPECIAL_CHARACTERS

    # Remove duplicate characters while preserving order
    characters = "".join(
        dict.fromkeys(characters)
    )

    return characters


# ============================================================
# MAXIMUM CALCULATION
# ============================================================

def calculate_total(
    charset_size,
    min_length,
    max_length
):

    total = 0

    for length in range(
        min_length,
        max_length + 1
    ):

        try:

            total += charset_size ** length

        except OverflowError:

            return float("inf")

    return total


# ============================================================
# GENERATOR
# ============================================================

def generate_combinations(
    characters,
    min_length,
    max_length,
    maximum,
    output_file
):

    total_generated = 0

    start_time = time.perf_counter()

    try:

        with open(
            output_file,
            "w",
            encoding="ascii",
            buffering=16 * 1024 * 1024
        ) as output:

            for length in range(
                min_length,
                max_length + 1
            ):

                if total_generated >= maximum:
                    break

                print(
                    f"\n{CYAN}"
                    f"Generating length {length}..."
                    f"{RESET}"
                )

                generator = itertools.product(
                    characters,
                    repeat=length
                )

                while total_generated < maximum:

                    remaining = (
                        maximum
                        - total_generated
                    )

                    batch_size = min(
                        BATCH_SIZE,
                        remaining
                    )

                    batch = itertools.islice(
                        generator,
                        batch_size
                    )

                    lines = [
                        "".join(item)
                        for item in batch
                    ]

                    if not lines:
                        break

                    output.write(
                        "\n".join(lines)
                    )

                    output.write("\n")

                    total_generated += len(lines)

                    elapsed = (
                        time.perf_counter()
                        - start_time
                    )

                    speed = (
                        total_generated / elapsed
                        if elapsed > 0
                        else 0
                    )

                    print(
                        f"\rGenerated: "
                        f"{total_generated:,}"
                        f" | Speed: "
                        f"{speed:,.0f}/sec",
                        end="",
                        flush=True
                    )

                output.flush()

    except KeyboardInterrupt:

        print(
            "\n\n"
            f"{YELLOW}"
            "Generation stopped."
            f"{RESET}"
        )

        print(
            f"Generated: "
            f"{total_generated:,}"
        )

        print(
            f"Partial file: "
            f"{os.path.abspath(output_file)}"
        )

        return total_generated, False

    return total_generated, True


# ============================================================
# MAIN
# ============================================================

def main():

    clear_screen()

    banner()

    # --------------------------------------------------------
    # Length
    # --------------------------------------------------------

    while True:

        min_length = get_number(
            "Minimum length (1-16): "
        )

        if 1 <= min_length <= MAX_LENGTH:
            break

        print(
            f"{RED}"
            "Length must be between 1 and 16."
            f"{RESET}"
        )

    while True:

        max_length = get_number(
            "Maximum length (1-16): "
        )

        if (
            1 <= max_length <= MAX_LENGTH
            and max_length >= min_length
        ):
            break

        print(
            f"{RED}"
            "Maximum length must be >= "
            "minimum length and <= 16."
            f"{RESET}"
        )

    # --------------------------------------------------------
    # Character set
    # --------------------------------------------------------

    print()

    characters = build_charset()

    if not characters:

        print(
            f"\n{RED}"
            "You must select at least "
            "one character type."
            f"{RESET}"
        )

        return

    print()

    print(
        f"{GREEN}"
        f"Character set size: "
        f"{len(characters)}"
        f"{RESET}"
    )

    print(
        f"Characters: {characters}"
    )

    # --------------------------------------------------------
    # Output filename
    # --------------------------------------------------------

    print()

    while True:

        filename = input(
            "Enter output filename: "
        ).strip()

        if not filename:

            print(
                f"{RED}"
                "Filename cannot be empty."
                f"{RESET}"
            )

            continue

        break

    # Automatically add .lst
    if not filename.lower().endswith(".lst"):
        filename += ".lst"

    # --------------------------------------------------------
    # Maximum / MAX
    # --------------------------------------------------------

    print()

    while True:

        maximum_input = input(
            "Maximum entries to generate "
            "(number or MAX): "
        ).strip()

        if maximum_input.lower() == "max":

            maximum = calculate_total(
                len(characters),
                min_length,
                max_length
            )

            print()

            if maximum == float("inf"):

                print(
                    f"{YELLOW}"
                    "The maximum is extremely large "
                    "and cannot be represented safely "
                    "as a Python integer calculation."
                    f"{RESET}"
                )

                # Python integers actually support arbitrary
                # precision, so this normally won't occur.
                continue

            print(
                f"{YELLOW}"
                f"Maximum possible combinations: "
                f"{maximum:,}"
                f"{RESET}"
            )

            break

        try:

            maximum = int(
                maximum_input
            )

            if maximum > 0:
                break

            print(
                f"{RED}"
                "Enter a number greater than 0 "
                "or MAX."
                f"{RESET}"
            )

        except ValueError:

            print(
                f"{RED}"
                "Enter a valid number or MAX."
                f"{RESET}"
            )

    # --------------------------------------------------------
    # Confirmation
    # --------------------------------------------------------

    print()

    print(
        "============================================================"
    )

    print(
        f"Length range : "
        f"{min_length}-{max_length}"
    )

    print(
        f"Characters   : "
        f"{len(characters)}"
    )

    print(
        f"Maximum      : "
        f"{maximum:,}"
    )

    print(
        f"Output       : "
        f"{os.path.abspath(filename)}"
    )

    print(
        "============================================================"
    )

    confirm = ask_yes_no(
        "Start generation?"
    )

    if not confirm:

        print(
            f"{YELLOW}"
            "Generation cancelled."
            f"{RESET}"
        )

        return

    # --------------------------------------------------------
    # Generate
    # --------------------------------------------------------

    print()

    print(
        f"{CYAN}"
        "Starting generation..."
        f"{RESET}"
    )

    total, completed = generate_combinations(
        characters,
        min_length,
        max_length,
        maximum,
        filename
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    print()

    elapsed = 0

    # We don't have the exact timer here because the generator
    # handles interruption internally.
    print(
        "============================================================"
    )

    if completed:

        print(
            f"{GREEN}"
            "GENERATION COMPLETE"
            f"{RESET}"
        )

    else:

        print(
            f"{YELLOW}"
            "GENERATION STOPPED"
            f"{RESET}"
        )

    print(
        "============================================================"
    )

    print(
        f"Generated : {total:,}"
    )

    print(
        f"File      : "
        f"{os.path.abspath(filename)}"
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            f"\n\n{YELLOW}"
            "Program interrupted."
            f"{RESET}"
        )

        sys.exit(0)
