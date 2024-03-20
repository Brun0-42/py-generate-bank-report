import os  
import argparse
import sys
import logging
import ofxparse


# ----------------------------------------------------------------------------#
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', metavar='<ofx input file>', type=str,
                    help='ofx input file')
    group = parser.add_argument_group("Logging options")
    group.add_argument('-v', '--verbose', action='count', default=0,
                        dest="verbose",
                        help="increase output verbosity (1: warning / 2: info / 3: debug).")
    return parser.parse_args()

# ----------------------------------------------------------------------------#
def check_arguments(args):

    if not os.path.isfile(args.input_file):
        print("{} is not a file".format(args.input_file))
        return False

    filename, file_extension = os.path.splitext(args.input_file)
    if file_extension != ".ofx":
        print("{} is not a ofx file".format(args.input_file))
        return False

    return True

# ----------------------------------------------------------------------------#
def print_arguments(args):
    print("arguments:")
    print("  * input_file: {}".format(args.input_file))
    print("  * verbose   : {}".format(args.verbose))

# ----------------------------------------------------------------------------#
def configure_logger(args):
    logging_handlers = [logging.StreamHandler(sys.stdout)]

    if args.verbose > 1:
        logger_filename="{}.log".format(os.path.splitext(os.path.basename(__file__))[0])
        f = open(logger_filename, "a")
        f.write("# ----------------------------------------------------------------------------#\n")
        f.write("# Start {} at {}\n".format(os.path.basename(__file__), datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")))
        f.write("# ----------------------------------------------------------------------------#\n")
        f.close()
        logging_handlers.append(logging.FileHandler(logger_filename))
                        
    FORMAT = '%(asctime)s [%(levelname)-8s] %(name)s: %(message)s'
    logging.basicConfig(handlers=logging_handlers, format=FORMAT, level=logging.ERROR)
    logger = logging.getLogger('iot-bridge-upgrade')

    if args.verbose == 1:
        logger.setLevel(logging.WARNING)
    elif args.verbose == 2:
        logger.setLevel(logging.INFO)
    elif args.verbose >= 3:
        logger.setLevel(logging.DEBUG)

    return logger

# ------------------------------------------------------------------------------
def generate_report(input_file):
    with open(input_file, 'rb') as fileobj:
            ofx = ofxparse.OfxParser.parse(fileobj)

    account = ofx.account
    # print(account.account_id)        # The account number
    # print(account.number)            # The account number (deprecated -- returns account_id)
    # print(account.routing_number)    # The bank routing number
    # print(account.branch_id)         # Transit ID / branch number
    # print(account.type)              # An AccountType object
    # print(account.statement)         # A Statement object
    # print(account.institution)       # An Institution object

    # Statement

    statement = account.statement
    # print(statement.start_date)          # The start date of the transactions
    # print(statement.end_date)            # The end date of the transactions
    # print(statement.balance)             # The money in the account as of the statement date


    data = dict()
    amont = dict()
    total = 0

    for transaction in statement.transactions:
        year = transaction.date.strftime('%Y')
        month = transaction.date.strftime('%m')

        if year in data:
            if month in data[year]:
                data[year][month].append(transaction)
                amont[year][month] += float(transaction.amount)
                total += float(transaction.amount)
            else:
                data[year][month] = []
                amont[year][month] = 0.0
                data[year][month].append(transaction)
                amont[year][month] += float(transaction.amount)
                total += float(transaction.amount)
        else:
            data[year] = dict()
            amont[year] = dict()
            data[year][month] = []
            amont[year][month] = 0.0
            data[year][month].append(transaction)
            amont[year][month] += float(transaction.amount)
            total += float(transaction.amount)

    f = open("report.md", "w")

    f.write("# Report\n")
    f.write("\n")

    f.write("## Resume\n\n")
    f.write("total: {}\n\n".format(total))
    f.write("|year|month|amont|\n")
    f.write("|---|---|---|\n")
    for year in data:
        for month in data[year]:
            f.write("|{}|{}|{}|\n".format(year, month, amont[year][month]))
    f.write("\n")

    f.write("## Details\n\n")
    N = 3
    for year in data:
        for month in data[year]:
            top = sorted(data[year][month], key=lambda x: x.amount, reverse = True)[:N]
            bottom = sorted(data[year][month], key=lambda x: x.amount)[:N]

            f.write("### {}/{}\n\n".format(year, month))
            f.write("\t* top:\n\n")
            f.write("|Date|amount|memo|\n")
            f.write("|---|---|---|\n")
            for transaction in top:
                if  transaction.amount > 0:
                    memo = ' '.join(transaction.memo.split())
                    f.write("|{}|{}|{}|\n".format(transaction.date, transaction.amount, memo))
            f.write("\n")
            f.write("\t* bottom:\n\n")
            f.write("|Date|amount|memo|\n")
            f.write("|---|---|---|\n")
            for transaction in bottom:
                if transaction.amount <= 0:
                    memo = ' '.join(transaction.memo.split())
                    f.write("|{}|{}|{}|\n".format(transaction.date, transaction.amount, memo))
            f.write("\n")

    f.close()

# ------------------------------------------------------------------------------
if __name__== "__main__":
    args = parse_arguments()
    if not check_arguments(args):
        sys.exit(1)

    logger = configure_logger(args)

    if args.verbose > 1:
        print_arguments(args)

    generate_report(args.input_file)

    print("Generate report: Done")

