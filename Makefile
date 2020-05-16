.PHONY: all test clean

.PHONY: add-resin-remote
add-resin-remote:
	git remote add resin gh_mafrosis@git.balena-cloud.com:gh_mafrosis/fridge.git
	git fetch --all

.PHONY: deploy-resin
deploy-resin:
	git push -f resin master
