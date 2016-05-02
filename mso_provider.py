import player_config

class MSOProvider:

    def __init__(self, mso_name, mso_id):
        self.mso_id = mso_id
        self.mso_name = mso_name

    def get_mso_id(self):
        return self.mso_id
    def get_mso_name(self):
        return self.mso_name

def get_mso_provider(provider_name):
    providers_soup = player_config.get_providers_data()
    providers = providers_soup.findall('.//providersItem')
    for provider in providers:
        if provider_name == provider.find('.//name').text:
            return MSOProvider(provider_name, provider.find('.//abbreviation').text)
    return None
