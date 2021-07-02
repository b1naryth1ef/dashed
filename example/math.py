import dashed


@dashed.command()
async def add(ctx: dashed.InteractionContext, x: int, y: int):
    await ctx.reply(f"{x+y}")
