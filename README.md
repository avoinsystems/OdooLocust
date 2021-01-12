# OdooLocust

An Odoo load testing solution, using odoolib and Locust

## Links

* odoolib: <a href="https://github.com/odoo/odoo-client-lib">odoo-client-lib</a>
* Locust: <a href="http://locust.io">locust.io</a>
* Odoo: <a href="https://odoo.com">odoo.com</a>

# Fork Changes

With the forked repository, the naming standards have been slightly altered. TaskSets are now called OdooUsers to better describe what they are.

# HowTo

To load test Odoo, you can create multiple tasks by extending the OdooUser class. Note that you will need to specify the `wait_time` property in order to more accurately simulate "real" users, which have small pauses between actions:

```
from locust import task, between
from OdooUser import OdooUser


class MyOdooUser(OdooUser):
    wait_time = between(15, 50)

    def on_start(self):
        self.menu = self._load_menu()
        self.randomlyChooseMenu()

    @task(10)
    def read_partners(self):
        cust_model = self.client.get_model('res.partner')
        cust_ids = cust_model.search([])
        prtns = cust_model.read(cust_ids)
        
    @task(5)
    def read_products(self):
        prod_model = self.client.get_model('product.product')
        ids = prod_model.search([])
        prods = prod_model.read(ids)
        
    @task(20)
    def create_so(self):
        prod_model = self.client.get_model('product.product')
        cust_model = self.client.get_model('res.partner')
        so_model = self.client.get_model('sale.order')
        
        cust_id = cust_model.search([('name', 'ilike', 'fletch')])[0]
        prod_ids = prod_model.search([('name', 'ilike', 'ipad')])
        
        order_id = so_model.create({
            'partner_id': cust_id,
            'order_line': [(0,0,{'product_id': prod_ids[0], 
                                 'product_uom_qty':1}),
                           (0,0,{'product_id': prod_ids[1], 
                                 'product_uom_qty':2}),
                          ],
            
        })
        so_model.action_button_confirm([order_id,])
```

and run your locust tests the usual way:

```
locust -f my_file.py MyOdooUser
```
# Generic test

This version is shipped with a configurable OdooUser that can be configured from local variables, and a generic odoo user which randomly clicks on menu items, 
OdooGenericUser.  To use the OdooGenericUser version, when running locust, simply specify the file


```
locust -f OdooGenericUser.py OdooGenericUser
```

# Environment variables

The following is a list of environment variables that, when set, will be used to configure Locust for Odoo

| Variable | Purpose | Default value |
|-|-|-|
| OL_HOST | The host IP of Odoo | "127.0.0.1" |
| OL_PORT | The port on which to expose Locust | 8069 |
| OL_DB_NAME | Name of the Odoo database | "demo" |
| OL_LOGIN | Odoo Login to use | "admin" |
| OL_PASSWORD | Odoo password to use | "admin" |
| OL_PROTOCOL | RPC protocol to use. Typically should not be changed. | "jsonrpc" |
| OL_USER_ID | The default user ID to use.  | -1 |
