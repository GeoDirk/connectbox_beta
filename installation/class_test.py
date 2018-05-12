# -*- coding: utf-8 -*-

class Pages:
    page_none,page_main, page_bat, page_info, page_stats = range(5)

def main():
    page = Pages.page_none
    print("Pages.page_none:" + str(page))
    page += 1
    print("Pages++:" + str(page))
    page += 1
    print("Pages++:" + str(page))
    page = page + 1
    print("Pages++:" + str(page))
    page = page + 1
    print("Pages++:" + str(page))
    page = page + 1
    print("Pages++:" + str(page))
    page = page + 1
    print("Pages++:" + str(page))
    

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass