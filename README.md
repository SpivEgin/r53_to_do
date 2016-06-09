# r53_to_do
Migrate DNS entries from Route 53 to Digital Ocean

Installation:

1. clone the code
    * git clone git@github.com:commoncode/r53_to_do.git
2. create virtualenv
3. install requirements
    * pip install -Ur requirements.txt
4. Add your Digital Ocean secret key as an environment variable
5. You may also need to install/configure the AWS CLI 
    * http://docs.aws.amazon.com/cli/latest/userguide/installing.html

Run:

Run the script in your terminal by calling the script and passing the domain that you are migrating as an argument.

```
python transfer_dns_records_script.py <domain-name>
```


