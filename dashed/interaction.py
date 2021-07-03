import asyncio
from dashed.loader import DashedContext
import dataclasses
from typing import Any, Dict
from .discord import (
    ApplicationCommandCallbackData,
    InteractionResponseType,
    WebhookEditBody,
)


class InteractionContext:
    def __init__(self, ctx: DashedContext, data: Dict[str, Any]):
        self.ctx = ctx
        self.data = data

    def reply(self, **kwargs):
        return {
            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": dataclasses.asdict(ApplicationCommandCallbackData(**kwargs)),
        }

    def defer(self, fn):
        asyncio.ensure_future(fn(DeferredInteractionContext(self)))
        return {
            "type": InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
        }


class DeferredInteractionContext:
    def __init__(self, original_interaction_context):
        self.original_interaction_context = original_interaction_context

    @property
    def ctx(self):
        return self.original_interaction_context.ctx

    @property
    def data(self):
        return self.original_interaction_context.data

    async def update(self, **kwargs):
        await self.ctx.client.edit_original_interaction_response(
            self.data["application_id"],
            self.data["token"],
            dataclasses.asdict(WebhookEditBody(**kwargs)),
        )
