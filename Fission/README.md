### Document all details for fission deployment - Lixinqian YU

- bomharvester: Harvester Data from BOM every 30 minutes
- epaharvester: Harvester Data from EPA every 1 hour
- auharvester: Harvester from Mastodon AU sever
- socialharvester: Harvester from Mastodon SOCIAL sever

1. Zip your Package
````
(
  cd Fission/functions/<name of directory>
  zip -r <name of directory>.zip .
  mv <name of directory>.zip ../
)

````

2. Create YAML specifications for your package and function
````
(
  cd Fission
  fission package create --sourcearchive ./functions/<name of directory>.zip \
    --spec\
    --env python \
    --name <pkg-name> \
    --buildcmd './build.sh'

  fission fn create --name <fn-name> \
    --spec\
    --pkg  <pkg-name> \
    --env python \
    --entrypoint "<fn-name>.main"
)
````

3. Create RestFul API 
````
(
  cd Fission
  fission route create --spec --name <router-name> --function <fn-name> \
    --method GET \
    --url <url-name>
  )
````

4. Apply Specs to k8s
````
fission spec apply --specdir fission/specs --wait
````