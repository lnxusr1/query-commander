import logging
import json

from core.config import settings as cfg
from core.helpers import encrypt
from core.tokenizer import tokenizer

def process_request(request, response):

    command = str(request.json_data.get("command", "auth")).lower()
    tokenizer.set_token(request.token)
    tokenizer.set_username(request.username)
    tokenizer.set_remote_addr(request.host)

    if command == "check":
        # check: allow browser to check if session is still valid (does not auto-extend session length)
        # check-init: same as "check" but if a valid token is found it auto-extends the session length
        if not tokenizer.validate():
            response.output({ "ok": False, "logout": True }, extend=False)
            return
        else:
            if request.json_data.get("extend", False):
                username = tokenizer.username
                logging.debug(f"[{username}@{tokenizer.remote_addr}] Session extended - {tokenizer.token}")
                tokenizer.update() # Auto extend session
            
            response.output({ 
                "ok": True, 
                "username": tokenizer.username,
                #"roles": [tokenizer.role_selected], # tokenizer.roles as list
                #"role_selected": tokenizer.role_selected, 
                "connections": tokenizer.connections()
            }, extend=False)

            return

    if command == "login":
        from core.authenticator import authenticator

        username = str(request.json_data.get("username", "")).strip()[0:100]
        password = str(request.json_data.get("password", ""))[0:256]

        if authenticator.validate(username, password):

            if len(authenticator.roles) == 0:
                # No roles for this login.
                response.output({ "ok": False })
                return

            tokenizer.set_username(username)
            tokenizer.set("username", username)
            tokenizer.set("roles", authenticator.roles)
            tokenizer.set("connections", tokenizer.connections())
            resp_data = { "ok": True, "username": tokenizer.username, "roles": authenticator.roles, }

            resp_data["role_selected"] = authenticator.roles[0]
            tokenizer.set("role_selected", resp_data["role_selected"])
            resp_data["connections"] = tokenizer.connections()
            if len(resp_data["connections"]) == 0:
                response.output({ "ok": False, "error": "No connections." })
                return

            if authenticator.use_token:
                tokenizer.set(
                    "credentials", 
                    encrypt(
                        tokenizer.safe_password, 
                        json.dumps({ "username": str(username), "password": str(password)[0:256]})
                    )
                )

            #tokenizer.purge()
            if not tokenizer.update():
                logging.error(f"[{username}@{tokenizer.remote_addr}] Unable to create token")
                response.output({ "ok": False })
                return

            logging.info(f"[{username}@{tokenizer.remote_addr}] Login successful - {tokenizer.token}")

            # If only 1 role then return connections
            response.output(resp_data)
            return
        else:
            logging.debug(f"[{username}@{tokenizer.remote_addr}] Session extended - {tokenizer.token}")
            response.output({ "ok": False })
            return

    if command == "logout":
        logging.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] Logout successful - {tokenizer.token}")
        tokenizer.remove()
        response.output({ "ok": False, "logout": True })
        return

    # ==============================================================================================================================

    if not tokenizer.validate():
        username = tokenizer.username
        if username is None:
            logging.error(f"[{tokenizer.remote_addr}] Invalid token - {tokenizer.token}")
        else:
            logging.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] Failed validation - {tokenizer.token}")
        response.output({ "ok": False, "logout": True })
        return

    # ==============================================================================================================================
    # EVERYTHING BELOW THIS LINE MUST BE LOGGED IN WITH VALID TOKEN

    if command == "select-role":
        for role_name in tokenizer.roles:
            if role_name == str(request.json_data.get("role", "")):
                tokenizer.set("role_selected", role_name)
                tokenizer.update()
                logging.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] Role changed to {role_name} - {tokenizer.token}")
                response.output({ "ok": True, "connections": tokenizer.connections })
                return

        logging.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] Role not found - {tokenizer.token}")
        response.output({ "ok": False })
        return

    if command == "get-profile":
        try:
            prf = tokenizer.get_profiler()

            tabs = prf.get("tabs", [])
            page_settings = prf.get("settings", {})

            response.output({
                "ok": True,
                "tabs": tabs,
                "settings": page_settings
            })

        except:
            response.output({ "ok": False })
        
        return

    if command == "save-profile":
        try:
            prf = tokenizer.get_profiler()

            prf.set("tabs", request.json_data.get("tabs", []))
            prf.set("settings", request.json_data.get("settings", {}))
            ret = prf.update()

            response.output({
                "ok": ret
            })

        except:
            response.output({ "ok": False })

        return

    if command == "delete-profile":
        try:
            prf = tokenizer.get_profiler()
            ret = prf.remove()

            response.output({
                "ok": ret
            })

        except:
            response.output({ "ok": False })

        return

    if command == "meta":
        #logging.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] meta request [{tokenizer.token}]")
        from functions.meta import get_info
        return get_info(request, response, "meta")

    if command == "ddl":
        #logging.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] ddl request [{tokenizer.token}]")
        from functions.meta import get_info
        return get_info(request, response, "ddl")

    if command == "details":
        #logging.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] detail request [{tokenizer.token}]")
        from functions.meta import get_info
        return get_info(request, response, "details")

    if command == "query":
        #logging.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] detail request [{tokenizer.token}]")
        from functions.query import get_query_results
        return get_query_results(
            response, 
            request.json_data.get("connection"), 
            request.json_data.get("database"), 
            request.json_data.get("statement"), 
            request.json_data.get("type"),
            int(request.json_data.get("row_count", 0))
        )

    # Default response... not valid, client should initiate logout procedures
    logging.error(f"Invalid request from {request.host}")
    response.output({ "ok": False, "logout": True })
    return
