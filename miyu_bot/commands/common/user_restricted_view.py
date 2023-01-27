from typing import Iterable

import discord


class UserRestrictedView(discord.ui.View):
    def __init__(self, allowed_users: Iterable[int], **kwargs):
        self.allowed_users = {*allowed_users}
        if "timeout" not in kwargs:  # Set a higher default timeout
            kwargs["timeout"] = 1200
        super(UserRestrictedView, self).__init__(**kwargs)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in self.allowed_users:
            await interaction.response.send_message(
                "This is not your message.", ephemeral=True
            )
            return False
        return True
