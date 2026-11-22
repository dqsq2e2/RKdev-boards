// SPDX-License-Identifier: GPL-2.0+
#include <asm/gpio.h>
#include <dm.h>
#include <linux/delay.h>
#include <power/regulator.h>

int rk_board_late_init(void)
{
    struct udevice *dev;
    struct gpio_desc *slot_perst;
    const char *const controls[] = { "wifi_enable" };
    int i, ret;

    /* BV2 U8100 shares PERST# and its external clock supply across x2+x2. */
    ret = gpio_hog_lookup_name("pcie3-slot-perst", &slot_perst);
    if (ret)
        return ret;
    ret = dm_gpio_set_value(slot_perst, 0);
    if (ret)
        return ret;
    ret = regulator_get_by_platname("vcc3v3_pcie30", &dev);
    if (ret)
        return ret;
    ret = regulator_set_enable_if_allowed(dev, true);
    if (ret)
        return ret;
    /* PI6C557 supplies both PHY reference clocks and the slot clock. */
    mdelay(100);
    ret = dm_gpio_set_value(slot_perst, 1);
    if (ret)
        return ret;
    mdelay(100);
    printf("I3588 PCIe3: slot x2+x2, shared PERST# released\n");

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
