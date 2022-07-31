from quicksight_api.config.config import Config
from mangum import Mangum

from quicksight_api.main.main import create_app, initialize_app

config = Config(
    cognito_aws_region="",
    cognito_user_pool_id="",
    cognito_web_client_id="",
)
app = create_app(config=config)
initialize_app(app=app)

handler = Mangum(app)
