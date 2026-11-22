// SPDX-License-Identifier: GPL-2.0+
#include <dm.h>
#include <dm/uclass.h>
#include <i2c.h>
#include <linux/delay.h>

#define NCA9555_ADDR 0x20
#define NCA9555_OUTPUT0 0x02
#define NCA9555_CONFIG0 0x06
#define USB_POWER_MASK (BIT(0) | BIT(1) | BIT(7))

static int aiot3588a2_update_power(struct udevice *bus, u8 reg, bool high)
{
    u8 data[] = { reg, 0 };
    struct i2c_msg msgs[] = {
        { .addr = NCA9555_ADDR, .len = 1, .buf = data },
        { .addr = NCA9555_ADDR, .flags = I2C_M_RD, .len = 1, .buf = data + 1 },
    };
    int ret;

    ret = i2c_get_ops(bus)->xfer(bus, msgs, ARRAY_SIZE(msgs));
    if (ret)
        return ret;
    if (high)
        data[1] |= USB_POWER_MASK;
    else
        data[1] &= ~USB_POWER_MASK;
    msgs[0].len = sizeof(data);
    return i2c_get_ops(bus)->xfer(bus, msgs, 1);
}

int rockchip_early_misc_init_r(void)
{
    struct udevice *bus;
    int i, ret;

    ret = uclass_get_device_by_ofnode(UCLASS_I2C, ofnode_path("/i2c@fec80000"), &bus);
    if (!ret) {
        /* Set output latches first and leave the other expander lines intact. */
        for (i = 0; i < 10; i++) {
            ret = aiot3588a2_update_power(bus, NCA9555_OUTPUT0, true);
            if (!ret)
                ret = aiot3588a2_update_power(bus, NCA9555_CONFIG0, false);
            if (!ret)
                break;
            mdelay(20);
        }
        if (!ret)
            mdelay(100);
    }
    if (ret)
        printf("AIOT-3588A V2.0: USB host power setup failed (%d)\n", ret);
    return 0;
}
