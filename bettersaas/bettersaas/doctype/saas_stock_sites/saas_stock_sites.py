import frappe

domain = frappe.conf.get("domain")
from frappe.model.document import Document
import os

log = open("some file.txt", "a")
from frappe.utils import random_string


def getSiteConfig():
    siteConfig = frappe.get_doc("SaaS settings")
    return siteConfig


def insertSite(site_name, admin_password):
    site = frappe.new_doc("SaaS stock sites")
    site.subdomain = site_name
    site.admin_password = admin_password
    site.insert()


def create_multiple_sites_in_parallel(commands, db_values):
    print("creating multiple sites in parallel")
    from subprocess import Popen

    processes = [Popen(cmd, shell=True, stdout=log, stderr=log) for cmd in commands]


def deleteSite(sitename):
    from subprocess import Popen

    config = getSiteConfig()
    command = "bench drop-site {} --force --no-backup --db-root-password {}".format(
        sitename, config.db_password
    )
    process = Popen(command, shell=True, stdout=log)
    process.wait()
    if domain != "localhost":
        os.system(
            "echo {} | sudo -S sudo service nginx reload".format(config.root_password)
        )
    print(process.returncode)


@frappe.whitelist()
def deleteUsedSites():
    sites = frappe.db.get_list("SaaS stock sites", filters={"isUsed": "yes"})
    for site in sites:
        deleteSite(site.subdomain + "." + domain)
    frappe.db.delete("SaaS stock sites", filters={"isUsed": "yes"})
    return "Deleted test sites"


@frappe.whitelist()
def refreshStockSites(*args, **kwargs):
    # this function runs every day and maintains the stock site
    print("refreshing stock sites")
    config = getSiteConfig()
    commands = []
    currentStock = frappe.db.get_list("SaaS stock sites", filters={"is_used": "no"})
    print("In stock", len(currentStock))
    db_values = []
    if len(currentStock) < int(config.stock_site_count):
        number_of_sites_to_stock = int(config.stock_site_count) - len(currentStock)
        for _ in range(number_of_sites_to_stock):
            subdomain = random_string(10)
            adminPassword = random_string(5)
            this_command = []
            this_command.append(
                "bench new-site {} --install-app erpnext  --admin-password {} --db-root-password {}".format(
                    subdomain + "." + domain, adminPassword, config.db_password
                )
            )
            apps_to_install = frappe.get_doc("SaaS settings").apps_to_install.split(",")
            for app in apps_to_install:
                this_command.append(
                    "bench --site {} install-app {}".format(
                        subdomain + "." + domain, app.strip()
                    )
                )

            this_command.append(
                "bench --site {} install-app clientside".format(
                    subdomain + "." + domain
                )
            )
            adminSubdomain = frappe.conf.get("admin_subdomain")
            this_command.append(
                "bench --site {} execute bettersaas.bettersaas.doctype.saas_stock_sites.saas_stock_sites.insertSite --args \"'{}','{}'\"".format(
                    adminSubdomain + "." + domain, subdomain, adminPassword
                )
            )
            site_defaults = frappe.get_doc("SaaS settings")
            this_command.append(
                "bench --site {} set-config max_users {}".format(
                    subdomain + "." + domain, site_defaults.default_user_limit
                )
            )
            this_command.append(
                "bench --site {} set-config max_email_limit {}".format(
                    subdomain + "." + domain, site_defaults.default_email_limit
                )
            )

            command = " ; ".join(this_command)
            print("ADDED COMMAND", command)
            commands.append(command)
            db_values.append([subdomain, adminPassword])
    # frappe.enqueue(create_multiple_sites_in_parallel,commands=commands,db_values=db_values,is_async=True,job_name="create_multiple_sites_in_parallel",at_front=True)
    create_multiple_sites_in_parallel(commands, db_values)
    return "Database will be updated soon with stock sites "


class SaaSstocksites(Document):
    pass