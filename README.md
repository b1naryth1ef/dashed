# dashed

simple sdk for creating and executing Discord slash commands and rich interactions.

## example

```python
import asyncio
import dashed


@dashed.command(description="It's like an echo chamber in here!")
async def echo(ctx: dashed.InteractionContext, message: str):
    return ctx.reply(content=message)


@dashed.command(description="Add two numbers")
async def sum(ctx: dashed.InteractionContext, x: int, y: int):
    return ctx.reply(content=f"Result: `{x + y}`")


@dashed.command(description="Suprise")
async def boo(ctx: dashed.InteractionContext):
    async def later(ctx: dashed.DeferredInteractionContext):
        await asyncio.sleep(5)
        await ctx.update(content="Boo!")

    # We can decide here whether to respond or defer
    return ctx.defer(later)


@dashed.command(description="Deferred by default")
async def deferred(ctx: dashed.DeferredInteractionContext, message: str):
    # Because we receive a "DeferredInteractionContext", this will always be deferred
    await asyncio.sleep(5)
    await ctx.update(content="It works")
```

## running

```sh
$ python -m dashed --load-from-file example/math.py --bind 0.0.0.0:8689
```