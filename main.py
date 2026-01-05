import subprocess
import platform

def clear_screen():
    if platform.system() == "Windows":
        subprocess.run(["cls"], shell=True)
    else:
        subprocess.run(["clear"], shell=True)


if __name__ == "__main__":
    clear_screen()
    while True:
        command = input("""
1. Scan images for ISBN 
2. Insert book from ISBN 
3. Insert books in pmb

0.exit
\\>:""")
    
        if command == "0":
            exit()
        elif(command == "1"):
            print(1)
        elif command == "2":
            print(2)
        elif command == "3":
            print(3)
        else :
            print("invalide input")
        