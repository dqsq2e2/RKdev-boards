// SPDX-License-Identifier: GPL-2.0+
#include <dm.h>
#include <linux/delay.h>
#include <power/regulator.h>

int rk_board_late_init(void)
{
    struct udevice *dev;
    const char *const controls[] = { "wifi_enable" };
    int i, ret;

    /* Reset peripheral state even when the previous OS left firmware active. */
    for (i = 0; i < ARRAY_SIZE(controls); i++) {
        ret = regulator_get_by_platname(controls[i], &dev);
        if (ret)
            return ret;
        ret = regulator_set_enable(dev, false);
        if (ret && ret != -EALREADY)
            return ret;
        mdelay(50);
        ret = regulator_set_enable(dev, true);
        if (ret)
            return ret;
    }
    return 0;
}
