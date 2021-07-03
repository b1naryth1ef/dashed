import dashed


@dashed.command(description="It's like an echo chamber in here!")
async def echo(ctx: dashed.InteractionContext, message: str):
    return ctx.reply(content=message)
