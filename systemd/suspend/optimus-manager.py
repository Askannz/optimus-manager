#!/usr/bin/env python3
import sys
from optimus_manager.hooks import pre_suspend, post_resume


def main():

    try:
        state = sys.argv[1]  # pre or post
        _mode = sys.argv[2] # suspend, hibernate or hybrid-sleep
    except IndexError:
        print("Not enough arguments")
        sys.exit(1)

    if state == "pre":
        pre_suspend.main()
    elif state == "post":
        post_resume.main()
    else:
        print(f"Invalid first argument: {state}")
        sys.exit(1)


if __name__ == "__main__":
    main()
