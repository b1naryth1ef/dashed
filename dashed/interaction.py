import dataclasses
from dashed.discord import ApplicationCommandCallbackData, InteractionResponseType


class InteractionContext:
    def reply(self, **kwargs):
        return {
            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": dataclasses.asdict(ApplicationCommandCallbackData(**kwargs)),
        }
