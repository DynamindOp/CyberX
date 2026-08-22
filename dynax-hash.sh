#!/usr/bin/env bash

# ============================================================
#                    DYNAX HASHING
# ============================================================

APP_NAME="DYNAX HASHING"
VERSION="1.0"
DB_FILE="hash_db.lst"

# Colors
RESET='\033[0m'
CYAN='\033[36m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
GRAY='\033[90m'


# ============================================================
# UI
# ============================================================

clear_screen() {
    clear 2>/dev/null || true
}

banner() {
    echo -e "${CYAN}"
    cat <<'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                    DYNAX HASHING                             ║
║                                                              ║
║              Secure Password Hash Utility                    ║
║                                                              ║
║                       v1.0                                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${RESET}"
}

section() {
    echo
    echo -e "${CYAN}┌──────────────────────────────────────────────────────────────┐"
    printf "│ %-60s │\n" "$1"
    echo -e "└──────────────────────────────────────────────────────────────┘${RESET}"
    echo
}

success() {
    echo -e "${GREEN}✓ $1${RESET}"
}

error_msg() {
    echo -e "${RED}✗ $1${RESET}"
}

info() {
    echo -e "${GRAY}• $1${RESET}"
}


# ============================================================
# DATABASE
# ============================================================

create_database() {

    if [[ ! -f "$DB_FILE" ]]; then

        touch "$DB_FILE"

        success "$DB_FILE created successfully."

        info "Hashes will be appended to this database."

        echo
        read -rp "Press ENTER to continue..."
    fi
}


# ============================================================
# HASH GENERATION
# ============================================================

generate_hash() {

    section "CREATE NEW HASH"

    read -rp "Identifier / username: " identifier

    if [[ -z "$identifier" ]]; then
        error_msg "Identifier cannot be empty."
        return
    fi

    read -rsp "Password: " password
    echo

    if [[ -z "$password" ]]; then
        error_msg "Password cannot be empty."
        return
    fi

    read -rsp "Confirm password: " confirmation
    echo

    if [[ "$password" != "$confirmation" ]]; then
        error_msg "Passwords do not match."
        return
    fi

    # Generate random salt
    salt=$(openssl rand -hex 32 2>/dev/null)

    if [[ -z "$salt" ]]; then
        error_msg "OpenSSL is required."
        return
    fi

    # PBKDF2-HMAC-SHA256
    hash=$(printf '%s' "$password" |
        openssl kdf \
        -kdfopt digest:SHA256 \
        -kdfopt "pass:$password" \
        -kdfopt "salt:$salt" \
        -kdfopt iter:600000 \
        PBKDF2 2>/dev/null |
        xxd -p -c 256)

    if [[ -z "$hash" ]]; then

        # Fallback using sha256sum with salt.
        # This is NOT equivalent to PBKDF2 but keeps
        # the utility functional on systems lacking
        # the required OpenSSL KDF interface.

        hash=$(printf '%s:%s' "$salt" "$password" |
            sha256sum |
            awk '{print $1}')

        algorithm="SHA256-FALLBACK"

    else

        algorithm="PBKDF2-HMAC-SHA256"
    fi

    record_id=$(openssl rand -hex 8)

    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Format:
    #
    # ID|IDENTIFIER|ALGORITHM|SALT|HASH|DATE
    #

    printf '%s|%s|%s|%s|%s|%s\n' \
        "$record_id" \
        "$identifier" \
        "$algorithm" \
        "$salt" \
        "$hash" \
        "$timestamp" >> "$DB_FILE"

    unset password
    unset confirmation

    success "Hash generated successfully."

    echo
    echo "Identifier : $identifier"
    echo "Algorithm  : $algorithm"
    echo "Record ID  : $record_id"
    echo "Created    : $timestamp"

    echo

    info "Password itself was not stored."
}


# ============================================================
# LIST RECORDS
# ============================================================

list_records() {

    section "HASH DATABASE"

    if [[ ! -s "$DB_FILE" ]]; then

        info "Database is empty."

        return
    fi

    printf "${CYAN}%-18s %-25s %-28s %-20s${RESET}\n" \
        "ID" \
        "IDENTIFIER" \
        "ALGORITHM" \
        "CREATED"

    echo "-----------------------------------------------------------------------------------------"

    while IFS='|' read -r id identifier algorithm salt hash timestamp
    do

        printf "%-18s %-25s %-28s %-20s\n" \
            "$id" \
            "$identifier" \
            "$algorithm" \
            "$timestamp"

    done < "$DB_FILE"

    echo

    info "Passwords are never displayed."
}


# ============================================================
# SHOW HASH
# ============================================================

show_hash() {

    section "SHOW STORED HASH"

    if [[ ! -s "$DB_FILE" ]]; then
        info "Database is empty."
        return
    fi

    read -rp "Identifier / username: " identifier

    found=0

    while IFS='|' read -r id user algorithm salt hash timestamp
    do

        if [[ "$user" == "$identifier" ]]; then

            found=1

            echo
            echo -e "${YELLOW}Record${RESET}"
            echo "----------------------------------------"
            echo "ID         : $id"
            echo "Identifier : $user"
            echo "Algorithm  : $algorithm"
            echo "Salt       : $salt"
            echo "Hash       : $hash"
            echo "Created    : $timestamp"
            echo

        fi

    done < "$DB_FILE"

    if [[ "$found" == "0" ]]; then
        error_msg "Identifier not found."
    fi
}


# ============================================================
# DATABASE INFORMATION
# ============================================================

database_info() {

    section "DATABASE INFORMATION"

    records=0

    if [[ -f "$DB_FILE" ]]; then
        records=$(grep -cve '^$' "$DB_FILE")
    fi

    size=0

    if [[ -f "$DB_FILE" ]]; then
        size=$(du -h "$DB_FILE" | awk '{print $1}')
    fi

    echo "Database : $(realpath "$DB_FILE" 2>/dev/null || echo "$DB_FILE")"
    echo "Records  : $records"
    echo "Size     : $size"
}


# ============================================================
# DELETE RECORD
# ============================================================

delete_record() {

    section "DELETE RECORD"

    if [[ ! -s "$DB_FILE" ]]; then
        info "Database is empty."
        return
    fi

    read -rp "Identifier / username: " identifier

    if ! grep -q "|$identifier|" "$DB_FILE"; then

        error_msg "Identifier not found."

        return
    fi

    echo
    echo -e "${YELLOW}Matching records:${RESET}"
    echo

    grep "|$identifier|" "$DB_FILE" |
        cut -d'|' -f1,2,6

    echo

    read -rp "Delete ALL records for this identifier? [y/N]: " confirm

    if [[ "${confirm,,}" != "y" ]]; then

        info "Deletion cancelled."

        return
    fi

    temp_file="${DB_FILE}.tmp"

    grep -v "|$identifier|" "$DB_FILE" > "$temp_file"

    mv "$temp_file" "$DB_FILE"

    success "Records deleted."
}


# ============================================================
# HELP
# ============================================================

help_menu() {

    section "COMMANDS"

    cat <<'EOF'

[1] Create Hash
    Generate and store a new password hash.

[2] List Records
    Display stored identifiers.

[3] Show Hash
    Display stored hash information.

[4] Delete Record
    Remove records from the database.

[5] Database Info
    Show database statistics.

[6] Help
    Display this menu.

[7] Exit
    Exit DYNAX HASHING.

EOF
}


# ============================================================
# MAIN MENU
# ============================================================

main_menu() {

    while true
    do

        echo -e "${CYAN}"
        cat <<'EOF'
╔══════════════════════════════════════════════════════════════╗
║                         MAIN MENU                            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] Create Hash                                             ║
║  [2] List Records                                            ║
║  [3] Show Hash                                               ║
║  [4] Delete Record                                           ║
║  [5] Database Info                                           ║
║  [6] Help                                                    ║
║  [7] Exit                                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
        echo -e "${RESET}"

        read -rp "DYNAX ❯ " choice

        case "$choice" in

            1)
                generate_hash
                ;;

            2)
                list_records
                ;;

            3)
                show_hash
                ;;

            4)
                delete_record
                ;;

            5)
                database_info
                ;;

            6)
                help_menu
                ;;

            7)
                echo
                success "DYNAX HASHING closed."
                exit 0
                ;;

            *)
                error_msg "Invalid option."
                ;;

        esac

        echo
        read -rp "Press ENTER to continue..."
        clear_screen
        banner

    done
}


# ============================================================
# START
# ============================================================

clear_screen
banner

create_database

main_menu
