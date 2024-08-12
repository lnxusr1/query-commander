import sys
import logging
import json

from core.config import settings as cfg
from core.helpers import encrypt
from core.interactions import Response
from core.tokenizer import tokenizer

def process_request(request):
    command = str(request.json_data.get("command", "auth")).lower()
    tokenizer.set_token(request.token)
    tokenizer.set_remote_addr(request.host)

    if command == "check":
        # check: allow browser to check if session is still valid (does not auto-extend session length)
        # check-init: same as "check" but if a valid token is found it auto-extends the session length
        resp = Response()
        if not tokenizer.validate():
            resp.output({ "ok": False, "logout": True })
            sys.exit()
        else:
            if request.json_data.get("extend", False):
                username = tokenizer.username
                logging.debug(f"[{username}@{tokenizer.remote_addr}] Session extended - {tokenizer.token}")
                tokenizer.update() # Auto extend session
            
            resp.output({ 
                "ok": True, 
                "username": tokenizer.username,
                #"roles": [tokenizer.role_selected], # tokenizer.roles as list
                #"role_selected": tokenizer.role_selected, 
                "connections": tokenizer.connections()
            })

            sys.exit()

    if command == "login":
        from core.authenticator import authenticator

        resp = Response()
        username = str(request.json_data.get("username", ""))[0:100]
        password = str(request.json_data.get("password", ""))[0:256]

        if authenticator.validate(username, password):

            if len(authenticator.roles) == 0:
                # No roles for this login.
                resp.output({ "ok": False })
                sys.exit()

            tokenizer.set("username", username)
            tokenizer.set("roles", authenticator.roles)
            tokenizer.set("connections", tokenizer.connections())
            resp_data = { "ok": True, "username": tokenizer.username, "roles": authenticator.roles, }

            #if len(authenticator.roles) > 1:
            #    resp_data["role_selected"] = ""
            #    tokenizer.set("role_selected", resp_data["role_selected"])
            #    resp_data["connections"] = []
            #else:    
            #    resp_data["role_selected"] = authenticator.roles[0]
            #    tokenizer.set("role_selected", resp_data["role_selected"])
            #    resp_data["connections"] = tokenizer.connections
            #    if len(tokenizer.connections) == 0:
            #        # No roles for this login.
            #        resp.output({ "ok": False })
            #        sys.exit()
            resp_data["role_selected"] = authenticator.roles[0]
            tokenizer.set("role_selected", resp_data["role_selected"])
            resp_data["connections"] = tokenizer.connections()
            if len(resp_data["connections"]) == 0:
                resp.output({ "ok": False, "error": "No connections." })
                sys.exit()

            if authenticator.use_token:
                tokenizer.set(
                    "credentials", 
                    encrypt(
                        tokenizer.safe_password, 
                        json.dumps({ "username": str(username), "password": str(password)[0:256]})
                    )
                )

            tokenizer.purge()
            if not tokenizer.update():
                logging.error(f"[{username}@{tokenizer.remote_addr}] Unable to create token")
                resp.output({ "ok": False })
                sys.exit()

            logging.info(f"[{username}@{tokenizer.remote_addr}] Login successful - {tokenizer.token}")

            # If only 1 role then return connections
            resp.output(resp_data)
            sys.exit()
        else:
            logging.debug(f"[{username}@{tokenizer.remote_addr}] Session extended - {tokenizer.token}")
            resp.output({ "ok": False })
            sys.exit()

    if command == "logout":
        resp = Response()
        logging.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] Logout successful - {tokenizer.token}")
        tokenizer.remove()
        resp.output({ "ok": False, "logout": True })
        sys.exit()

    # ==============================================================================================================================

    if not tokenizer.validate():
        resp = Response()
        username = tokenizer.username
        if username is None:
            logging.error(f"[{tokenizer.remote_addr}] Invalid token - {tokenizer.token}")
        else:
            logging.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] Failed validation - {tokenizer.token}")
        resp.output({ "ok": False, "logout": True })
        sys.exit()

    # ==============================================================================================================================
    # EVERYTHING BELOW THIS LINE MUST BE LOGGED IN WITH VALID TOKEN

    if command == "select-role":
        resp = Response()
        for role_name in tokenizer.roles:
            if role_name == str(request.json_data.get("role", "")):
                tokenizer.set("role_selected", role_name)
                tokenizer.update()
                logging.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] Role changed to {role_name} - {tokenizer.token}")
                resp.output({ "ok": True, "connections": tokenizer.connections })
                sys.exit()

        logging.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] Role not found - {tokenizer.token}")
        resp.output({ "ok": False })
        sys.exit()

    if command == "get-profile":
        try:
            prf = tokenizer.get_profiler()
            resp = Response()

            tabs = prf.get("tabs", [])
            page_settings = prf.get("settings", {})

            resp.output({
                "ok": True,
                "tabs": tabs,
                "settings": page_settings
            })

        except:
            resp.output({ "ok": False })
        
        sys.exit()

    if command == "save-profile":
        try:
            prf = tokenizer.get_profiler()
            resp = Response()

            prf.set("tabs", request.json_data.get("tabs", []))
            prf.set("settings", request.json_data.get("settings", {}))
            ret = prf.update()

            resp.output({
                "ok": ret
            })

        except:
            resp.output({ "ok": False })

        sys.exit()

    if command == "delete-profile":
        try:
            prf = tokenizer.get_profiler()
            resp = Response()

            ret = prf.remove()

            resp.output({
                "ok": ret
            })

        except:
            resp.output({ "ok": False })

        sys.exit()

    if command == "meta":
        #logging.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] meta request [{tokenizer.token}]")
        from functions.meta import get_info
        get_info(request, "meta")

    if command == "ddl":
        #logging.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] ddl request [{tokenizer.token}]")
        from functions.meta import get_info
        get_info(request, "ddl")

    if command == "details":
        #logging.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] detail request [{tokenizer.token}]")
        from functions.meta import get_info
        get_info(request, "details")

    if command == "query":
        #logging.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] detail request [{tokenizer.token}]")
        from functions.query import get_query_results
        get_query_results(
            request.json_data.get("connection"), 
            request.json_data.get("database"), 
            request.json_data.get("statement"), 
            request.json_data.get("type"),
            int(request.json_data.get("row_count", 0))
        )

    # Default response... not valid, client should initiate logout procedures
    logging.error(f"Invalid request from {request.host}")
    resp = Response()
    resp.output({ "ok": False, "logout": True })
    sys.exit()
