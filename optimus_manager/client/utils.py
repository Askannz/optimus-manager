
def ask_confirmation():

    ans = input("> ").lower()

    if ans == "y" or ans == "Y":
        return True
    elif ans == "n" or ans == "N":
        print("Aborting.")
        return False
    else:
        print("Invalid choice. Aborting")
        return False
