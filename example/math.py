import dashed


@dashed.command(description="add some numbers")
async def add(ctx: dashed.InteractionContext, x: int, y: int):
    return ctx.reply(content=f"{x+y}")
