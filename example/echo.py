import dashed


@dashed.command()
async def echo(ctx: dashed.InteractionContext, message: str):
    await ctx.reply(message)
