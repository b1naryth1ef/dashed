import dashed

math = dashed.Group("math", description="do some math")


@math.command(description="add some numbers")
async def add(ctx: dashed.InteractionContext, x: int, y: int):
    return ctx.reply(content=f"{x+y}")


config = math.subgroup("config", description="math config")


@config.command(description="set value")
async def set(ctx: dashed.InteractionContext, key: str, value: str):
    return ctx.reply(content="Set!")


@config.command(description="get value")
async def get(ctx: dashed.InteractionContext, key: str):
    return ctx.reply(content="Get!")
