// SPDX-License-Identifier: GPL-2.0+
#include <dm.h>
#include <dm/uclass.h>
#include <i2c.h>
#include <linux/delay.h>

#define NCA9555_ADDR 0x20
#define NCA9555_OUTPUT0 0x02
#define NCA9555_OUTPUT1 0x03
#define NCA9555_CONFIG0 0x06
#define NCA9555_CONFIG1 0x07
#define USB_POWER_MASK (BIT(0) | BIT(1) | BIT(7))
#define MODEM_RESET BIT(3)
#define MODEM_POWER BIT(5)
#define MODEM_DISABLE BIT(0) /* P1_0 */

static int aiot3588a2_update_bits(struct udevice *bus, u8 reg, u8 set, u8 clear)
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
    data[1] = (data[1] & ~clear) | set;
    msgs[0].len = sizeof(data);
    return i2c_get_ops(bus)->xfer(bus, msgs, 1);
}

static int aiot3588a2_enable_modem_slot(struct udevice *bus)
{
    int ret;

    /* Match the V2.0 factory levels: RESET low, DISABLE high, then POWER high. */
    ret = aiot3588a2_update_bits(bus, NCA9555_OUTPUT0, 0, MODEM_RESET);
    if (!ret)
        ret = aiot3588a2_update_bits(bus, NCA9555_OUTPUT1, MODEM_DISABLE, 0);
    if (!ret)
        ret = aiot3588a2_update_bits(bus, NCA9555_CONFIG0, 0, MODEM_RESET);
    if (!ret)
        ret = aiot3588a2_update_bits(bus, NCA9555_CONFIG1, 0, MODEM_DISABLE);
    if (!ret)
        ret = aiot3588a2_update_bits(bus, NCA9555_OUTPUT0, MODEM_POWER, 0);
    if (!ret)
        ret = aiot3588a2_update_bits(bus, NCA9555_CONFIG0, 0, MODEM_POWER);
    return ret;
}

int rockchip_early_misc_init_r(void)
{
    struct udevice *bus;
    int i, ret;

    ret = uclass_get_device_by_ofnode(UCLASS_I2C, ofnode_path("/i2c@fec80000"), &bus);
    if (!ret) {
        /* Set output latches first and leave the other expander lines intact. */
        for (i = 0; i < 10; i++) {
            ret = aiot3588a2_update_bits(bus, NCA9555_OUTPUT0, USB_POWER_MASK, 0);
            if (!ret)
                ret = aiot3588a2_update_bits(bus, NCA9555_CONFIG0, 0, USB_POWER_MASK);
            if (!ret)
                break;
            mdelay(20);
        }
        if (!ret) {
            int modem_ret = aiot3588a2_enable_modem_slot(bus);

            if (modem_ret)
                printf("AIOT-3588A V2.0: M.2 modem slot power setup failed (%d)\n", modem_ret);
            mdelay(100);
        }
    }
    if (ret)
        printf("AIOT-3588A V2.0: USB host power setup failed (%d)\n", ret);
    return 0;
}
