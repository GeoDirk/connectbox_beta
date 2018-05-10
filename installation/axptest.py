# -*- coding: utf-8 -*-

import axp209

if __name__ == "__main__":
    try:
        axp = axp209.AXP209()
        print("New HAT detected")
    except OSError as e:
        print("Old HAT detected")
    except KeyboardInterrupt:
        pass
