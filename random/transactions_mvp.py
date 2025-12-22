import datetime as dt
import os

import altair as alt
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DB_URL_TH", None)
if not DATABASE_URL:
    raise ValueError("Please set the DB_URL_TH environment variable.")
engine = create_engine(DATABASE_URL, future=True)


def fetch_df(sql, **params):
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def exec_sql(sql, **params):
    with engine.begin() as conn:
        conn.execute(text(sql), params)


def get_all_tags():
    return fetch_df("SELECT id, tag FROM tag ORDER BY tag;")


def ensure_tag(tag_name: str) -> int:
    tag_name = tag_name.strip()
    if not tag_name:
        raise ValueError("Empty tag name")

    row = fetch_df("SELECT id FROM tag WHERE tag = :t;", t=tag_name)
    if not row.empty:
        return int(row.iloc[0]["id"])

    with engine.begin() as conn:
        r = conn.execute(
            text("INSERT INTO tag(tag) VALUES (:t) RETURNING id;"),
            {"t": tag_name},
        )
        scalar = r.scalar()
        if scalar is None:
            raise ValueError("Failed to create tag")
        return scalar


st.set_page_config(page_title="Transaction History", layout="wide")

st.sidebar.header("Filters")
today = dt.date.today()
start_default = dt.date(today.year, 1, 1)
date_filter_enabled = st.sidebar.checkbox(
    "Filter by date",
    value=st.session_state.get("date_filter_enabled", False),
    key="date_filter_enabled",
)
date_from = None
date_to = None
if date_filter_enabled:
    date_range = st.sidebar.date_input(
        "Date range (posted)",
        value=st.session_state.get("date_range", (start_default, today)),
        key="date_range",
    )
    if isinstance(date_range, (list, tuple)):
        if len(date_range) == 2:
            date_from, date_to = date_range
        elif len(date_range) == 1:
            date_from = date_to = date_range[0]
    else:
        date_from = date_to = date_range

text_filter = st.sidebar.text_input(
    "Search text (note / counterparty)",
    value=st.session_state.get("text_filter", ""),
    key="text_filter",
)

payment_types = fetch_df("SELECT id, name FROM payment_type ORDER BY name;")
payment_type_filter = st.sidebar.multiselect(
    "Payment types",
    options=payment_types["name"].tolist(),
    default=st.session_state.get("payment_type_filter", []),
    key="payment_type_filter",
)

all_tags_df = get_all_tags()
tag_options = all_tags_df["tag"].tolist()
filter_txn_tags = st.sidebar.multiselect(
    "Transaction tags (any)",
    tag_options,
    default=st.session_state.get("filter_txn_tags", []),
    key="filter_txn_tags",
)
filter_acct_tags = st.sidebar.multiselect(
    "Account tags (any)",
    tag_options,
    default=st.session_state.get("filter_acct_tags", []),
    key="filter_acct_tags",
)

st.sidebar.markdown("---")
st.sidebar.subheader("Tag management")
new_tags_raw = st.sidebar.text_input("New tag(s) (comma-separated)", "")
if st.sidebar.button("Create tag(s)"):
    created = []
    for raw in new_tags_raw.split(","):
        t = raw.strip()
        if not t:
            continue
        try:
            ensure_tag(t)
            created.append(t)
        except Exception as e:
            st.sidebar.error(f"Error creating tag '{t}': {e}")
    if created:
        st.sidebar.success(f"Created: {', '.join(created)}")


where_clauses = []
params = {}
if date_filter_enabled and date_from is not None and date_to is not None:
    where_clauses.append("date_posted >= :dfrom")
    where_clauses.append("date_posted <= :dto")
    params["dfrom"] = date_from
    params["dto"] = date_to
if payment_type_filter:
    where_clauses.append("payment_type = ANY(:pt)")
    params["pt"] = payment_type_filter
if text_filter:
    where_clauses.append(
        "(note ILIKE :q OR counterparty_account_holder ILIKE :q OR counterparty_account_number ILIKE :q)"
    )
    params["q"] = f"%{text_filter}%"
if filter_txn_tags:
    where_clauses.append("tags && :t_tags")
    params["t_tags"] = filter_txn_tags
if filter_acct_tags:
    where_clauses.append("account_tags && :a_tags")
    params["a_tags"] = filter_acct_tags
WHERE = ""
if where_clauses:
    WHERE = "WHERE " + " AND ".join(where_clauses)

latest_df = fetch_df(
    "SELECT latest_date_posted, latest_date_paid, days_since_posted, days_since_paid FROM transaction_latest_dates;"
)
if not latest_df.empty:
    lp = latest_df.loc[0, "latest_date_posted"]
    lpa = latest_df.loc[0, "latest_date_paid"]
    dsp = int(pd.to_numeric(latest_df.loc[0, "days_since_posted"]))
    dspa = int(pd.to_numeric(latest_df.loc[0, "days_since_paid"]))
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Data recency**")
    st.sidebar.write(f"Latest posted: **{lp}** ({dsp} days ago)")
    st.sidebar.write(f"Latest paid: **{lpa}** ({dspa} days ago)")


tab_txn, tab_acct, tab_dash = st.tabs(["Transactions", "Accounts", "Dashboard"])

with tab_txn:
    st.subheader("Transactions & Tags")
    sql = f"""
        SELECT
            id, date_posted, payment_type, is_outgoing,
            signed_amount, amount_abs, fee, net_amount,
            counterparty_account_holder, counterparty_account_number,
            note, bank_transaction_id, tags, account_tags
        FROM transaction_enriched
        {WHERE}
        ORDER BY date_posted DESC, id DESC;
    """
    df = fetch_df(sql, **params)
    st.write(f"{len(df)} rows")
    if df.empty:
        st.info("No transactions in current filter.")
    else:
        df_display = df.copy()
        df_display["selected"] = False
        display_columns = [
            "selected",
            "id",
            "date_posted",
            "payment_type",
            "counterparty_account_holder",
            "counterparty_account_number",
            "note",
            "net_amount",
            "tags",
            "account_tags",
        ]
        cols = display_columns
        df_display = df_display[cols]
        edited = st.data_editor(
            df_display,
            width="stretch",
            hide_index=True,
            column_config={
                "selected": st.column_config.CheckboxColumn(
                    "Select",
                    help="Check to include this transaction in bulk tag actions",
                    default=False,
                ),
                "id": "ID",
                "date_posted": "Date posted",
                "payment_type": "Payment type",
                "counterparty_account_holder": "Account holder",
                "counterparty_account_number": "Account number",
                "note": "Note",
                "net_amount": st.column_config.NumberColumn(
                    "Net amount (CZK)",
                    format="%.2f",
                ),
                "tags": "Tags",
                "account_tags": "Account tags",
            },
        )
        selected_ids = edited.loc[edited["selected"], "id"].tolist()
        st.caption(f"Selected {len(selected_ids)} transaction(s): {selected_ids}")
        st.markdown("### Bulk tag assign (transactions)")
        add_tags = st.multiselect(
            "Add transaction tags",
            tag_options,
            key="txn_add_tags",
        )
        rem_tags = st.multiselect(
            "Remove transaction tags",
            tag_options,
            key="txn_rem_tags",
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Add tags to selected transactions"):
                if not selected_ids:
                    st.warning("No transactions selected.")
                else:
                    for tname in add_tags:
                        tag_id = ensure_tag(tname)
                        for tid in selected_ids:
                            exec_sql(
                                """
                                INSERT INTO transaction_tag(transaction_id, tag_id)
                                VALUES (:tid, :tg)
                                ON CONFLICT DO NOTHING;
                                """,
                                tid=int(tid),
                                tg=int(tag_id),
                            )
                    st.success("Tags added to selected transactions.")
        with col2:
            if st.button("Remove tags from selected transactions"):
                if not selected_ids:
                    st.warning("No transactions selected.")
                else:
                    for tname in rem_tags:
                        tag_row = fetch_df(
                            "SELECT id FROM tag WHERE tag = :t;", t=tname
                        )
                        if tag_row.empty:
                            continue
                        tag_id = int(tag_row.iloc[0]["id"])
                        for tid in selected_ids:
                            exec_sql(
                                """
                                DELETE FROM transaction_tag
                                WHERE transaction_id = :tid AND tag_id = :tg;
                                """,
                                tid=int(tid),
                                tg=tag_id,
                            )
                    st.success("Tags removed from selected transactions.")


with tab_acct:
    st.subheader("Accounts & Tags")
    acct_df = fetch_df(
        f"""
        SELECT
            counterparty_account_number AS account_number,
            counterparty_account_holder AS account_holder,
            COALESCE(
                SUM(
                    CASE WHEN is_outgoing THEN -signed_amount ELSE 0 END
                ),
                0
            ) AS total_sent,
            COALESCE(
                SUM(
                    CASE WHEN NOT is_outgoing THEN signed_amount ELSE 0 END
                ),
                0
            ) AS total_received,
            account_tags
        FROM transaction_enriched
        {WHERE}
        GROUP BY account_number, account_holder, account_tags
        ORDER BY account_holder NULLS LAST, account_number;
        """,
        **params,
    )
    st.write(f"{len(acct_df)} accounts")
    if acct_df.empty:
        st.info("No accounts for current filter.")
    else:
        acct_display = acct_df.copy()
        acct_display["selected"] = False
        display_cols = [
            "selected",
            "account_number",
            "account_holder",
            "total_sent",
            "total_received",
            "account_tags",
        ]
        acct_display = acct_display[display_cols]
        edited_accts = st.data_editor(
            acct_display,
            width="stretch",
            hide_index=True,
            column_config={
                "selected": st.column_config.CheckboxColumn(
                    "Select",
                    help="Check to include this account in bulk tag actions",
                    default=False,
                ),
                "account_number": "Account number",
                "account_holder": "Account holder",
                "total_sent": st.column_config.NumberColumn(
                    "Total sent (CZK)",
                    format="%.2f",
                ),
                "total_received": st.column_config.NumberColumn(
                    "Total received (CZK)",
                    format="%.2f",
                ),
                "account_tags": "Account tags",
            },
        )
        selected_accounts = edited_accts.loc[
            edited_accts["selected"], "account_number"
        ].tolist()
        st.caption(f"Selected {len(selected_accounts)} account(s): {selected_accounts}")
        st.markdown("### Bulk tag assign (accounts)")
        add_atags = st.multiselect(
            "Add account tags",
            tag_options,
            key="acct_add_tags",
        )
        rem_atags = st.multiselect(
            "Remove account tags",
            tag_options,
            key="acct_rem_tags",
        )
        col3, col4 = st.columns(2)
        with col3:
            if st.button("Add tags to selected accounts"):
                if not selected_accounts:
                    st.warning("No accounts selected.")
                else:
                    for acct_number in selected_accounts:
                        acc = fetch_df(
                            "SELECT id FROM account WHERE account_number = :n;",
                            n=acct_number,
                        )
                        if acc.empty:
                            continue
                        aid = int(acc.iloc[0]["id"])
                        for tname in add_atags:
                            tag_id = ensure_tag(tname)
                            exec_sql(
                                """
                                INSERT INTO account_tag(account_id, tag_id)
                                VALUES (:aid, :tg)
                                ON CONFLICT DO NOTHING;
                                """,
                                aid=aid,
                                tg=int(tag_id),
                            )
                    st.success("Account tags added to selected accounts.")

        with col4:
            if st.button("Remove tags from selected accounts"):
                if not selected_accounts:
                    st.warning("No accounts selected.")
                else:
                    for acct_number in selected_accounts:
                        acc = fetch_df(
                            "SELECT id FROM account WHERE account_number = :n;",
                            n=acct_number,
                        )
                        if acc.empty:
                            continue
                        aid = int(acc.iloc[0]["id"])
                        for tname in rem_atags:
                            tag_row = fetch_df(
                                "SELECT id FROM tag WHERE tag = :t;",
                                t=tname,
                            )
                            if tag_row.empty:
                                continue
                            tag_id = int(tag_row.iloc[0]["id"])
                            exec_sql(
                                """
                                DELETE FROM account_tag
                                WHERE account_id = :aid AND tag_id = :tg;
                                """,
                                aid=aid,
                                tg=tag_id,
                            )
                    st.success("Account tags removed from selected accounts.")


with tab_dash:
    st.subheader("Dashboard")
    totals_df = fetch_df(
        f"""
        SELECT
            COALESCE(
                SUM(
                    CASE WHEN is_outgoing THEN -signed_amount ELSE 0 END
                ),
                0
            ) AS total_spent,
            COALESCE(
                SUM(
                    CASE WHEN NOT is_outgoing THEN signed_amount ELSE 0 END
                ),
                0
            ) AS total_received
        FROM transaction_enriched
        {WHERE};
        """,
        **params,
    )
    if not totals_df.empty:
        total_spent = float(pd.to_numeric(totals_df.loc[0, "total_spent"]))
        total_received = float(pd.to_numeric(totals_df.loc[0, "total_received"]))
        st.markdown("### Totals for current filter")
        st.write(f"**Total spent:** {total_spent:,.2f} CZK")
        st.write(f"**Total received:** {total_received:,.2f} CZK")
    else:
        st.info("No data for current filter.")
    st.markdown("---")
    mdf = fetch_df(
        f"""
        SELECT
            date_trunc('month', date_posted) AS month,
            SUM(net_amount) AS net_amount
        FROM transaction_enriched
        {WHERE}
        GROUP BY 1
        ORDER BY 1;
        """,
        **params,
    )
    st.subheader("Monthly net flow")
    if not mdf.empty:
        chart_df = mdf.copy()
        chart = (
            alt.Chart(chart_df)
            .mark_bar()
            .encode(
                x=alt.X("month:T", title="Month"),
                y=alt.Y("net_amount:Q", title="Net amount (CZK)"),
                color=alt.condition(
                    alt.datum.net_amount >= 0,
                    alt.value("#4CAF50"),
                    alt.value("#F44336"),
                ),
                tooltip=["month:T", "net_amount:Q"],
            )
            .properties(height=350)
        )
        st.altair_chart(chart, width="stretch")
    else:
        st.info("No data for monthly net flow with current filter.")
