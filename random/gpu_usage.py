import asyncio
import os


class GpuInfo:
    def __init__(
        self,
        usage,
        temp,
        power_draw,
        memory_used,
        memory_free,
        utilization_memory,
        utilization_encoder,
        utilization_decoder,
        utilization_jpeg,
        utilization_ofa,
        name,
        pstate,
        memory_total,
        power_max_limit,
        power_min_limit,
    ):
        self.usage = usage
        self.temp = temp
        self.power_draw = power_draw
        self.memory_used = memory_used
        self.memory_free = memory_free
        self.utilization_memory = utilization_memory
        self.utilization_encoder = utilization_encoder
        self.utilization_decoder = utilization_decoder
        self.utilization_jpeg = utilization_jpeg
        self.utilization_ofa = utilization_ofa
        self.name = name
        self.pstate = pstate
        self.memory_total = memory_total
        self.power_max_limit = power_max_limit
        self.power_min_limit = power_min_limit
        self.temp_units = "°C"
        self.memory_units = "MiB"
        self.utilization_units = "%"
        self.power_units = "W"

    def __repr__(self):
        return (
            f"{self.name}: {self.usage:.1f}% GPU, {self.temp:.1f}{self.temp_units}, {self.power_draw:.1f}{self.power_units}, "
            f"{self.memory_used:.1f}/{self.memory_total:.1f}{self.memory_units} ({self.memory_free:.1f}{self.memory_units} free), "
            f"{self.utilization_memory:.1f}{self.utilization_units} memory, {self.utilization_encoder:.1f}{self.utilization_units} encoder, "
            f"{self.utilization_decoder:.1f}{self.utilization_units} decoder, {self.utilization_jpeg:.1f}{self.utilization_units} jpeg, "
            f"{self.utilization_ofa:.1f}{self.utilization_units} ofa, {self.pstate}, {self.power_min_limit:.1f}-{self.power_max_limit:.1f}{self.power_units}"
        )


async def get_static_gpu_info():
    result = (
        os.popen(
            "nvidia-smi --query-gpu=name,memory.total,power.max_limit,power.min_limit --format=csv,noheader,nounits"
        )
        .read()
        .strip()
    )
    if result:
        name, memory_total, power_max_limit, power_min_limit = result.split(", ")
        return name, float(memory_total), float(power_max_limit), float(power_min_limit)
    return None, None, None, None


async def get_dynamic_gpu_info(freq):
    while True:
        result = (
            os.popen(
                "nvidia-smi --query-gpu=utilization.gpu,temperature.gpu,power.draw,memory.used,memory.free,utilization.memory,utilization.encoder,utilization.decoder,utilization.jpeg,utilization.ofa,pstate --format=csv,noheader,nounits"
            )
            .read()
            .strip()
        )
        if result:
            values = result.split(", ")
            values[:10] = map(float, values[:10])
            yield values
        else:
            yield [None] * 11
        await asyncio.sleep(freq)


async def retrieve_gpu_info(frequency=1):
    name, memory_total, power_max_limit, power_min_limit = await get_static_gpu_info()
    async for dynamic_values in get_dynamic_gpu_info(frequency):
        (
            gpu_usage,
            gpu_temp,
            power_draw,
            memory_used,
            memory_free,
            utilization_memory,
            utilization_encoder,
            utilization_decoder,
            utilization_jpeg,
            utilization_ofa,
            pstate,
        ) = dynamic_values
        yield GpuInfo(
            gpu_usage,
            gpu_temp,
            power_draw,
            memory_used,
            memory_free,
            utilization_memory,
            utilization_encoder,
            utilization_decoder,
            utilization_jpeg,
            utilization_ofa,
            name,
            pstate,
            memory_total,
            power_max_limit,
            power_min_limit,
        )


def draw_bar(value, min_value, max_value, width):
    return "█" * int((value - min_value) / (max_value - min_value) * width) + "-" * (
        width - int((value - min_value) / (max_value - min_value) * width)
    )


def print_gpu_info(gpu: GpuInfo):
    t_size = os.get_terminal_size()
    width = t_size.columns
    output = f"┌{'─'*(width-2)}┐\n"
    output += f"│{gpu.name}{" "*(width-len(gpu.name)-2)}│\n"
    output += f"├{'─'*(width-2)}┤\n"
    output += f"│{'GPU Usage:':<15}{gpu.usage:>4.0f} %   {draw_bar(gpu.usage, 0, 100, int(width-(width/2)))} [100 %]{' '*(int(width/2)-34)}│\n"
    output += f"│{'Temperature:':<15}{gpu.temp:>4.0f} °C  {draw_bar(gpu.temp, 0, 100, int(width-(width/2)))} [100 °C]{' '*(int(width/2)-35)}│\n"
    output += f"│{'Power Draw:':<15}{gpu.power_draw:>4.0f} W   {draw_bar(gpu.power_draw,gpu.power_min_limit, gpu.power_max_limit, int(width-(width/2)))} [{int(gpu.power_max_limit)} W]{' '*(int(width/2)-34)}│\n"
    output += f"│{'Memory Usage:':<15}{int(gpu.memory_used):>4.0f} MiB {draw_bar(gpu.memory_used, 0, gpu.memory_total, int(width-(width/2)))} [{int(gpu.memory_total)} MiB]{' '*(int(width/2)-37)}│\n"
    output += f"│{'Power State:':<15}{gpu.pstate:>4}{' '*(width-21)}│\n"
    output += f"└{'─'*(width-2)}┘\n"
    print(output, end="\033[F" * 9)


async def main():
    async for gpu_info in retrieve_gpu_info(frequency=0.1):
        print_gpu_info(gpu_info)


if __name__ == "__main__":
    asyncio.run(main())
