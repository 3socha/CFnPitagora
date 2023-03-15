include .env

AWS_REGION := us-west-2

install:
	poetry install

src/requirements.txt: pyproject.toml poetry.lock
	poetry export --without-hashes > src/requirements.txt

build: src/requirements.txt
	poetry run sam build --use-container

run: build
	poetry run sam local invoke \
		--region $(AWS_REGION) \
		--event events/post.json
# poetry run sam local invoke \
# 	--region $(AWS_REGION) \
# 	--event events/get.json

deploy: build
	sam deploy

test-remote:
	curl -s $(FUNCTION_URL) -w '\n'
	curl -s -XPOST $(FUNCTION_URL) -H "Content-Type: application/json" -H "API-Key: $(APY_KEY)" -d "{\"message\": \"test tweet $(shell date)\"}"  -w '\n'

destroy:
	sam delete

put-params:
	@aws ssm put-parameter --name /twitter/consumer_key        --type SecureString --value $(CONSUMER_KEY)
	@aws ssm put-parameter --name /twitter/consumer_secret     --type SecureString --value $(CONSUMER_SECRET)
	@aws ssm put-parameter --name /twitter/access_token        --type SecureString --value $(ACCESS_TOKEN)
	@aws ssm put-parameter --name /twitter/access_token_secret --type SecureString --value $(ACCESS_TOKEN_SECRET)
	@aws ssm put-parameter --name /twitter/api_key             --type SecureString --value $(APY_KEY)
