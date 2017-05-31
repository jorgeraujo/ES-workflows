import boto3

simpleDB = boto3.client('sdb')
event = {"account": "lucia", "ammount": "0"}


def lambda_handler(event):
    print("hello")
    print(float(event["ammount"]))


    if float(event["ammount"]) > 5:
        update_credit = float(event["ammount"])-5
        u_credit = str(update_credit)
        itemname = event["account"]
        
        response = simpleDB.put_attributes(
            DomainName='ESWorkflows',
            ItemName=itemname,
            Attributes=[
                {
                    'Name': 'Credit',
                    'Value': u_credit,
                    'Replace': True
                },
            ]
        )
        print(u_credit)
        return {"credit" : u_credit}
    return {"credit" : -1 }

    return "END"

if __name__ == '__main__':
    lambda_handler(event)
