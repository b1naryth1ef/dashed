import asyncio
import dataclasses
from typing import Any, Dict
from .discord import (
    ApplicationCommandCallbackData,
    DiscordAPIClient,
    InteractionResponseType,
    WebhookEditBody,
)


class InteractionContext:
    def __init__(self, api: DiscordAPIClient, data: Dict[str, Any]):
        self.api = api
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
    def api(self):
        return self.original_interaction_context.api

    @property
    def data(self):
        return self.original_interaction_context.data

    async def update(self, **kwargs):
        await self.api.edit_original_interaction_response(
            self.data["application_id"],
            self.data["token"],
            dataclasses.asdict(WebhookEditBody(**kwargs)),
        )
