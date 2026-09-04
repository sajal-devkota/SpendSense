import streamlit as st

from frontend.api_client import ApiClientError, get_current_user, login_user, register_user


st.set_page_config(
    page_title="SpendSense",
    page_icon="💰",
    layout="wide",
)


def initialize_session() -> None:
    st.session_state.setdefault("access_token", None)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("authentication_message", None)


def clear_session() -> None:
    st.session_state.access_token = None
    st.session_state.user = None


def show_login() -> None:
    st.subheader("Log in")

    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Log in", use_container_width=True)

    if not submitted:
        return

    if not email.strip() or not password:
        st.error("Email and password are required.")
        return

    try:
        result = login_user(email.strip(), password)
    except ApiClientError as exc:
        st.error(exc.message)
        return

    st.session_state.access_token = result["access_token"]
    st.session_state.user = result["user"]
    st.session_state.authentication_message = "You are now logged in."
    st.rerun()


def show_registration() -> None:
    st.subheader("Create an account")

    with st.form("registration_form"):
        username = st.text_input("Username", key="registration_username")
        email = st.text_input("Email", key="registration_email")
        password = st.text_input("Password", type="password", key="registration_password")
        confirmation = st.text_input(
            "Confirm password",
            type="password",
            key="registration_confirmation",
        )
        submitted = st.form_submit_button("Create account", use_container_width=True)

    if not submitted:
        return

    if not username.strip() or not email.strip() or not password:
        st.error("Username, email, and password are required.")
        return

    if password != confirmation:
        st.error("Passwords do not match.")
        return

    try:
        register_user(username.strip(), email.strip(), password)
    except ApiClientError as exc:
        st.error(exc.message)
        return

    st.success("Account created successfully. You can now log in.")


def show_authentication() -> None:
    st.title("SpendSense")
    st.caption("Track, Manage, and make sense of your spending.")

    login_tab, register_tab = st.tabs(["Log in", "Register"])
    with login_tab:
        show_login()
    with register_tab:
        show_registration()


def validate_session() -> bool:
    token = st.session_state.access_token
    if not token:
        return False

    try:
        st.session_state.user = get_current_user(token)
        return True
    except ApiClientError as exc:
        if exc.status_code == 401:
            clear_session()
            st.session_state.authentication_message = exc.message
            return False

        st.error(exc.message)
        st.info("Start the FastAPI server, then refresh this page.")
        st.stop()


def show_authenticated_app() -> None:
    user = st.session_state.user

    with st.sidebar:
        st.subheader("SpendSense")
        st.write(f"Signed in as **{user['username']}**")
        if st.button("Log out", use_container_width=True):
            clear_session()
            st.session_state.authentication_message = "You have been logged out."
            st.rerun()

    st.title(f"Welcome, {user['username']}")
    st.write("Your expense dashboard will be added here next.")


initialize_session()

authenticated = validate_session()
message = st.session_state.authentication_message
if message:
    st.info(message)
    st.session_state.authentication_message = None

if authenticated:
    show_authenticated_app()
else:
    show_authentication()

