import string
import hashlib
import requests
import secrets
import json
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich import print
from rich.theme import Theme
from rich.console import Console
from rich.table import Table

theme = Theme({"success": "bold green", "fail": "bold red"})
console = Console(theme=theme)


def main():

    vault = open_vault()

    masterpass = inquirer.secret("Enter your master password: ").execute()
    masterpass = validate_masterpass(masterpass)
    console.print("Successfully saved the masterpass! ", style="success")

    action = call_to_action()

    while action != "Exit":
        if action == "Add New Credentials":
            vault = add_credentials(vault)
            console.print("Successfully added credentials! ", style="success")
            save_vault(vault)
            action = call_to_action()
        elif action == "Get Credentials":
            returned_user, returned_pass = get_credentials(masterpass, vault)
            print(f"\nUsername: {returned_user} \nPassword: {returned_pass}\n")
            save_vault(vault)
            action = call_to_action()
        elif action == "List All Credentials":
            list_credentials(masterpass, vault)
            save_vault(vault)
            action = call_to_action()
        elif action == "Edit Credentials":
            edit_credentials(masterpass, vault)
            save_vault(vault)
            action = call_to_action()
        elif action == "Delete Credentials":
            delete_credentials(masterpass, vault)
            save_vault(vault)
            action = call_to_action()
        elif action == "Check For Leaks":
            check_credentials(
                inquirer.secret("Enter the password to be checked: ").execute()
            )
            save_vault(vault)
            action = call_to_action()
        elif action == "Generate Password":
            password = generate_credentials()
            console.print(
                f"Your generated password is: [cyan]{password}[/cyan]", style="success"
            )
            save_vault(vault)
            action = call_to_action()

    save_vault(vault)
    print("[cyan][bold]Thank you for using this password manager tool! [/cyan][/bold]")


def open_vault(filename="vault.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    


def call_to_action():
    action = inquirer.select(
        message="Select a Choice: ",
        choices=[
            "Add New Credentials",
            "Get Credentials",
            "List All Credentials",
            "Edit Credentials",
            "Delete Credentials",
            "Check For Leaks",
            "Generate Password",
            "Exit",
        ],
        default=None,
    ).execute()

    return action


def validate_masterpass(m):
    m = str(m)
    digit_count = alpha_count = punc_count = upper_count = lower_count = 0
    for ch in m:
        if ch.isdigit():
            digit_count += 1
        elif ch.isalpha():
            alpha_count += 1
        elif ch in string.punctuation:
            punc_count += 1
        if ch.isupper():
            upper_count += 1
        elif ch.islower():
            lower_count += 1
    while (
        len(m) < 12
        or digit_count < 2
        or alpha_count < 4
        or punc_count < 1
        or upper_count < 1
        or lower_count < 1
    ):
        console.print(
            "Password must be at least 12 chars long and include 2 digits, 4 letters, 1 uppercase, 1 lowercase, and 1 special character.",
            style="fail",
        )
        digit_count = alpha_count = punc_count = upper_count = lower_count = 0
        m = inquirer.secret("Enter your master password: ", qmark="").execute()
        for ch in m:
            if ch.isdigit():
                digit_count += 1
            elif ch.isalpha():
                alpha_count += 1
            elif ch in string.punctuation:
                punc_count += 1
            if ch.isupper():
                upper_count += 1
            elif ch.islower():
                lower_count += 1
    return m


def check_masterpass(masterpass):
    master = inquirer.secret("Enter your masterpass: ", qmark="").execute()
    while master != masterpass:
        console.print("Wrong password! ", style="fail")
        master = inquirer.secret("Enter your masterpass: ", qmark="").execute()


def add_credentials(v):

    service = input("Enter the service name: ").lower()
    while service == "":
        console.print("Service name is required! ", style="fail")
        service = input("Enter the service name: ").lower()

    while service in v:
        console.print("Service already exists! ", style="fail")
        service = input("Enter the service name: ").lower()

    user = input("Enter the username: ")
    while user == "":
        console.print("Username is required! ", style="fail")
        user = input("Enter the username: ")

    passw = inquirer.secret("Enter the password: ", qmark="").execute()
    while passw == "":
        console.print("Password is required! ", style="fail")
        passw = inquirer.secret("Enter the password: ", qmark="").execute()

    new = {"username": user, "passw": passw}
    key = f"{service}"
    v[key] = new
    return v


def select_service(v):
    services = [s.capitalize() for s in list(v.keys())]
    service_choice = inquirer.select(
        message="Select a service: ",
        choices=services,
        default=None,
    ).execute()

    return service_choice.lower()


def get_credentials(masterpass, v):
    check_masterpass(masterpass)
    service_choice = select_service(v)

    return v[service_choice]["username"], v[service_choice]["passw"]


def list_credentials(masterpass, v):
    check_masterpass(masterpass)
    table = Table()
    table.add_column("Service", justify="center", style="cyan")
    table.add_column("Username", justify="center", style="cyan")
    table.add_column("Password", justify="center", style="cyan")
    for service in v:
        table.add_row(service.capitalize(), v[service]["username"], v[service]["passw"])
    console.print(table)


def edit_credentials(masterpass, v):
    check_masterpass(masterpass)
    service_choice = select_service(v)
    new_user = input("Enter the new username: ")
    new_pass = inquirer.secret("Enter the new password: ").execute()
    v[service_choice]["username"] = new_user
    v[service_choice]["passw"] = new_pass
    console.print("Successfully updated the credentials! ", style="success")


def delete_credentials(masterpass, v):
    check_masterpass(masterpass)
    service_choice = select_service(v)
    answ = console.input(
        f"[yellow]Are you sure you would like to delete [/yellow][cyan]{service_choice.capitalize()}[/cyan]? (yes/no) "
    )
    if answ.lower() == "yes":
        del v[service_choice]
        console.print("Successfully deleted the credentials! ", style="success")
    else:
        console.print("Deletion canceled.", style = "fail")


def check_credentials(pass_check):
    enc_pass = hashlib.sha1(pass_check.encode("utf-8")).hexdigest().upper()
    prefix = enc_pass[:5]
    suffix = enc_pass[5:]

    url = f"https://api.pwnedpasswords.com/range/{prefix}"

    try:
        response = requests.get(url, timeout=8)
        response.raise_for_status()
    except requests.RequestException:
        console.print(
            "Could not check leaks right now (network/API error).", style="fail"
        )
        return

    found = False
    count = 0

    for line in response.text.splitlines():
        try:
            api_suffix, api_count = line.split(":", 1)
        except ValueError:
            continue

        if api_suffix.strip().upper() == suffix:
            try:
                count = int(api_count.strip())
            except ValueError:
                count = api_count.strip()
            found = True
            break

    if found:
        console.print(
            f"Your password was found in a leak {count} times! ", style="fail"
        )
    else:
        console.print(f"Your password was not found in a leak! ", style="success")

def generate_credentials():
    choices = [
        Choice(value="lower", name="Lowercase letters (a-z)"),
        Choice(value="upper", name="Uppercase letters (A-Z)"),
        Choice(value="digits", name="Digits (0-9)"),
        Choice(value="special", name="Special characters (!@#$...)"),
    ]
    selected = inquirer.checkbox(
        message="Select the password features: ",
        choices=choices,
        validate=lambda result: len(result) >= 2
        or "Please select at least two options",
    ).execute()

    while not selected:
        
        console.print("You must select at least two options! ", style="fail")
        selected = inquirer.checkbox(
            message="Select the password features: ",
            choices=choices,
            validate=lambda result: len(result) >= 2
            or "Please select at least two options",
        ).execute()

    features = ""

    if "lower" in selected:
        features += string.ascii_lowercase
    if "upper" in selected:
        features += string.ascii_uppercase
    if "digits" in selected:
        features += string.digits
    if "special" in selected:
        features += string.punctuation

    password = "".join(secrets.choice(features) for _ in range(16))

    return password


def save_vault(vault, filename="vault.json"):
    with open(filename, "w") as f:
        json.dump(vault, f, indent=4)


if __name__ == "__main__":
    main()
