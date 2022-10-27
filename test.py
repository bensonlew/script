import sys
def run_script():
    print sys._getframe(1)

def main():
    run_script()

if __name__ == "__main__":
    main()
