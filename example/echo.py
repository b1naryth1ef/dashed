import asyncio
import dashed


@dashed.command(description="It's like an echo chamber in here!")
async def echo(ctx: dashed.InteractionContext, message: str):
    return ctx.reply(content=message)


@dashed.command(description="Suprise")
async def boo(ctx: dashed.InteractionContext):
    async def later(ctx: dashed.DeferredInteractionContext):
        await asyncio.sleep(5)
        await ctx.update(content="Boo!")

    return ctx.defer(later)


@dashed.command(name="channel-info", description="Get information about a channel")
async def channel_info(ctx: dashed.InteractionContext, channel: dashed.Channel):
    print(channel, ctx.data)
    return ctx.reply(content="Cool")
