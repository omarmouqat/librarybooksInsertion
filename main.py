
from conf import *
import time
from isbn_scanner import scan_images_for_ISBN

from general_utils import *
    
if __name__ == "__main__":
    
    while True:
        clear_screen()
        command = input("""
1. Scan images for ISBN 
2. Insert book from ISBN 
3. Insert books in pmb

0.exit
\\>:""")
    
        if command == "0":
            exit()
        elif(command == "1"):
            clear_screen()
            scan_images_for_ISBN()
            if input("Enter 0 to return to main menu\n") == "0":
                continue
        elif command == "2":
            print(2)
        elif command == "3":
            print(3)
        else :
            print("invalide input")
        
